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
