import unittest

from app.services.ingestion.parser import infer_title


class TitleExtractionTestCase(unittest.TestCase):
    def test_infer_title_merges_two_line_title_block(self) -> None:
        pages = [
            {
                "page_num": 1,
                "text": "\n".join(
                    [
                        "ODIN: Disentangled Reward",
                        "Mitigates Hacking in RLHF",
                        "Alice Smith, Bob Lee",
                        "Abstract",
                        "We study reward hacking in RLHF.",
                    ]
                ),
            }
        ]

        title = infer_title(pages=pages, fallback="fallback-title")

        self.assertEqual(title, "ODIN: Disentangled Reward Mitigates Hacking in RLHF")

    def test_infer_title_skips_top_noise_line_before_title(self) -> None:
        pages = [
            {
                "page_num": 1,
                "text": "\n".join(
                    [
                        "Published as a conference paper at ICLR 2025",
                        "Retrieval-Augmented Agents",
                        "for Open-Ended Planning",
                        "Jane Doe, John Roe",
                        "Abstract",
                    ]
                ),
            }
        ]

        title = infer_title(pages=pages, fallback="fallback-title")

        self.assertEqual(title, "Retrieval-Augmented Agents for Open-Ended Planning")

    def test_infer_title_ignores_preprint_arxiv_and_author_affiliation_lines(self) -> None:
        pages = [
            {
                "page_num": 1,
                "text": "\n".join(
                    [
                        "Preprint. Under review.",
                        "arXiv:2501.12345v2 [cs.LG] 10 Jan 2025",
                        "Context-Aware Distillation",
                        "for Long-Horizon Reasoning",
                        "Alice Smith1, Bob Lee2",
                        "1 University of Example",
                        "alice@example.edu",
                        "Abstract",
                    ]
                ),
            }
        ]

        title = infer_title(pages=pages, fallback="fallback-title")

        self.assertEqual(title, "Context-Aware Distillation for Long-Horizon Reasoning")

    def test_infer_title_stops_before_author_list_with_footnotes(self) -> None:
        pages = [
            {
                "page_num": 1,
                "text": "\n".join(
                    [
                        "ODIN: Disentangled Reward",
                        "Mitigates Hacking in RLHF",
                        "Lichang Chen*‡ Chen Zhu*† Davit Soselia‡",
                        "Abstract",
                    ]
                ),
            }
        ]

        title = infer_title(pages=pages, fallback="fallback-title")

        self.assertEqual(title, "ODIN: Disentangled Reward Mitigates Hacking in RLHF")
        self.assertNotIn("Lichang Chen", title)
        self.assertNotIn("*", title)


if __name__ == "__main__":
    unittest.main()
