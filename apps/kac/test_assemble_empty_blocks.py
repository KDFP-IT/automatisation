import unittest

from lxml import etree as xml

import assemble


def document(*blocks):
    root = xml.Element(assemble.qname("w", "document"), nsmap={"w": assemble.NS["w"]})
    body = xml.SubElement(root, assemble.qname("w", "body"))
    for number, content in enumerate(blocks, 1):
        divider = xml.SubElement(body, assemble.qname("w", "p"))
        props = xml.SubElement(divider, assemble.qname("w", "pPr"))
        xml.SubElement(props, assemble.qname("w", "sectPr"))
        run = xml.SubElement(divider, assemble.qname("w", "r"))
        xml.SubElement(run, assemble.qname("w", "t")).text = f"ПРАЙС-ЛИСТЫ К РАЗДЕЛУ КАЦ №{number}"
        block = xml.SubElement(body, assemble.qname("w", "p"))
        if content is not None:
            run = xml.SubElement(block, assemble.qname("w", "r"))
            xml.SubElement(run, assemble.qname("w", "t")).text = content
    xml.SubElement(body, assemble.qname("w", "sectPr"))
    return root


class EmptyOfferBlocksTest(unittest.TestCase):
    def test_manually_paginated_appendix_preserves_prefix_and_rebuilds_only_offers(self):
        doc = document(None)
        body = doc.find("w:body", assemble.NS)
        prefix = xml.Element(assemble.qname("w", "p"))
        xml.SubElement(xml.SubElement(prefix, assemble.qname("w", "r")), assemble.qname("w", "t")).text = "Введение"
        body.insert(0, prefix)
        heading = xml.SubElement(body, assemble.qname("w", "p"))
        body[-2].addprevious(heading)
        xml.SubElement(xml.SubElement(heading, assemble.qname("w", "r")), assemble.qname("w", "t")).text = "ПРАЙС ЛИСТЫ К РАЗДЕЛУ КАЦ №2 - Сеть"
        placeholder = xml.Element(assemble.qname("w", "p"))
        heading.addnext(placeholder)
        assemble.populate_empty_block(placeholder)
        before = xml.tostring(prefix)
        layout = assemble.prepare_layout(doc, {1: "Первый", 2: "Сеть", 3: "Мост"}, False)
        self.assertEqual(list(layout), [1, 2, 3])
        self.assertEqual(xml.tostring(body[0]), before)
        self.assertIn("№2 - Сеть", assemble.paragraph_text(heading))
        self.assertEqual(assemble.find_dividers(doc)[2], heading)

    def test_extra_text_in_manually_paginated_appendix_is_protected(self):
        doc = document("Авторское примечание")
        body = doc.find("w:body", assemble.NS)
        body[-1].addprevious(xml.Element(assemble.qname("w", "p")))
        before = xml.tostring(doc)
        with self.assertRaisesRegex(ValueError, "текст вне разделителя"):
            assemble.prepare_layout(doc, {1: "Сеть"}, False)
        self.assertEqual(xml.tostring(doc), before)

    def test_full_and_single_section(self):
        for single in (False, True):
            with self.subTest(single=single):
                doc = document(None)
                layout = assemble.prepare_layout(doc, {1: "Тест"}, single)
                block, runs = layout[1]
                self.assertEqual(runs, assemble.block_runs(block))
                self.assertIsNotNone(runs[0].find(".//a:blip", assemble.NS))

    def test_empty_block_can_be_template_for_new_sections(self):
        doc = document(None)
        layout = assemble.prepare_layout(doc, {1: "Первый", 2: "Второй"}, False)
        self.assertEqual(set(layout), {1, 2})
        for block, runs in layout.values():
            self.assertEqual(runs, assemble.block_runs(block))

    def test_text_is_never_replaced(self):
        for single in (False, True):
            with self.subTest(single=single):
                doc = document("Сохранить этот текст")
                with self.assertRaises(ValueError):
                    assemble.prepare_layout(doc, {1: "Тест"}, single)
                self.assertIn("Сохранить этот текст", "".join(doc.itertext()))

    def test_mixed_empty_and_existing_blocks_rejected(self):
        doc = document(None, None)
        second = assemble.find_dividers(doc)[2].getnext()
        assemble.populate_empty_block(second)
        with self.assertRaises(ValueError):
            assemble.prepare_layout(doc, {1: "Первый", 2: "Второй"}, False)


if __name__ == "__main__":
    unittest.main()
