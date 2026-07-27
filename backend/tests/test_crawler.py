"""Tests for the crawler service HTML parser."""

from app.services.crawler_service import _parse_products
import uuid


class TestParseProducts:
    def test_parses_valid_rows(self):
        html = """
        <table>
            <tbody>
                <tr>
                    <td>EPREL-001</td>
                    <td>Vitodens 200-W</td>
                    <td>A</td>
                    <td>Viessmann</td>
                </tr>
            </tbody>
        </table>
        """
        mfr_id = uuid.uuid4()
        cat_id = uuid.uuid4()
        products = _parse_products(html, mfr_id, cat_id)
        assert len(products) == 1
        assert products[0]["eprel_id"] == "EPREL-001"
        assert products[0]["manufacturer_id"] == mfr_id

    def test_skips_empty_rows(self):
        html = "<table><tbody></tbody></table>"
        products = _parse_products(html, uuid.uuid4(), uuid.uuid4())
        assert len(products) == 0

    def test_handles_no_table(self):
        html = "<div>No table here</div>"
        products = _parse_products(html, uuid.uuid4(), uuid.uuid4())
        assert len(products) == 0
