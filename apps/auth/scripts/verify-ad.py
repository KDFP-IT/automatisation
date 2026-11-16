#!/usr/bin/env python3
"""Preflight AD check from a host that sees the controller.

Binds as the given login (UPN) and verifies membership in each --group-dn
through LDAP_MATCHING_RULE_IN_CHAIN (nested groups count). Password is asked
interactively and never logged.

Run from the VPS (192.168.30.183 sees kdfp-dc1/kdfp-dc2):

  python3 scripts/verify-ad.py --url ldap://192.168.30.200:389 \\
      --base-dn DC=kdfp,DC=ru --domain kdfp.ru --login nikita_g \\
      --group-dn 'CN=KDFP-Portal-Users,OU=KDFP,DC=kdfp,DC=ru'
"""

import argparse
import getpass
import ssl
import sys
from urllib.parse import urlparse

IN_CHAIN = "1.2.840.113556.1.4.1941"


def main() -> int:
    args = parse_args()
    from ldap3 import Server, Connection, Tls
    from ldap3.utils.conv import escape_filter_chars

    parsed = urlparse(args.url)
    use_ssl = parsed.scheme.lower() == "ldaps"
    tls = None if args.no_tls else Tls(validate=ssl.CERT_REQUIRED,
                                       version=ssl.PROTOCOL_TLS_CLIENT)
    upn = args.login if "@" in args.login else f"{args.login}@{args.domain}"
    password = getpass.getpass(f"AD password for {upn}: ") if not args.password else args.password
    server = Server(parsed.hostname, port=parsed.port or None,
                    use_ssl=use_ssl, tls=tls, connect_timeout=args.timeout)
    conn = Connection(server, user=upn, password=password,
                      receive_timeout=args.timeout + 5, raise_exceptions=True)
    try:
        conn.open()
        if not use_ssl and not args.no_tls:
            conn.start_tls()
        if not conn.bind():
            print(f"BIND FAILED: {conn.result.get('description')}")
            return 1
        print(f"bind OK: {conn.extend.standard.who_am_i()}")
        conn.search(args.base_dn,
                    f"(userPrincipalName={escape_filter_chars(upn)})",
                    attributes=["distinguishedName"])
        if not conn.entries:
            print("user not found under base DN")
            return 1
        user_dn = str(conn.entries[0].distinguishedName)
        print(f"user DN: {user_dn}")
        failed = False
        for group_dn in args.group_dn:
            conn.search(group_dn,
                        f"(member:{IN_CHAIN}:={escape_filter_chars(user_dn)})",
                        search_scope="BASE", attributes=["cn"])
            ok = bool(conn.entries)
            failed |= args.require and not ok
            print(f"{'MEMBER' if ok else 'not member'}: {group_dn}")
        return 1 if failed else 0
    except Exception as problem:  # noqa: BLE001 - preflight script, print all
        print(f"ERROR: {problem}")
        return 2
    finally:
        conn.unbind()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify AD bind + group membership.")
    parser.add_argument("--url", required=True, help="ldaps://host:636 or ldap://host:389")
    parser.add_argument("--base-dn", required=True)
    parser.add_argument("--domain", default="kdfp.ru")
    parser.add_argument("--login", required=True)
    parser.add_argument("--group-dn", action="append", default=[])
    parser.add_argument("--require", action="store_true",
                        help="exit 1 unless member of every --group-dn")
    parser.add_argument("--no-tls", action="store_true",
                        help="skip STARTTLS/LDAPS (internal net opt-in)")
    parser.add_argument("--password", help="avoid prompt (scripts only)")
    parser.add_argument("--timeout", type=int, default=8)
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
