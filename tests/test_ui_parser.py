"""
Tests for UIParser: XML hierarchy parsing, centroid calculations,
token compression, and element filtering.
"""

import json
from android_mcp.ui_parser import UIParser, BOUNDS_REGEX

SAMPLE_COMPLEX_XML = """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<hierarchy rotation="0">
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.android.settings" bounds="[0,0][1080,2400]">
    <node index="0" text="" resource-id="com.android.settings:id/action_bar" class="android.view.ViewGroup" package="com.android.settings" bounds="[0,120][1080,260]">
      <node index="0" text="Settings" resource-id="android:id/title" class="android.widget.TextView" package="com.android.settings" clickable="false" bounds="[60,150][300,230]" />
      <node index="1" text="" content-desc="Search settings" resource-id="com.android.settings:id/search_button" class="android.widget.ImageButton" package="com.android.settings" clickable="true" bounds="[940,140][1040,240]" />
    </node>
    <node index="1" text="" resource-id="android:id/list" class="android.widget.ListView" package="com.android.settings" scrollable="true" bounds="[0,260][1080,2200]">
      <node index="0" text="Network &amp; internet" resource-id="com.android.settings:id/network_title" class="android.widget.TextView" package="com.android.settings" clickable="true" bounds="[180,300][900,420]" />
      <node index="1" text="Connected devices" resource-id="com.android.settings:id/bluetooth_title" class="android.widget.TextView" package="com.android.settings" clickable="true" bounds="[180,440][900,560]" />
      <node index="2" text="Airplane mode" resource-id="android:id/title" class="android.widget.TextView" package="com.android.settings" clickable="false" bounds="[180,580][700,700]" />
      <node index="3" text="" resource-id="com.android.settings:id/airplane_switch" class="android.widget.Switch" package="com.android.settings" checkable="true" checked="false" clickable="true" bounds="[880,600][1020,680]" />
      <node index="4" text="" resource-id="" class="android.view.View" package="com.android.settings" clickable="false" bounds="[0,700][1080,702]" />
    </node>
  </node>
</hierarchy>"""


class TestUIParserBounds:
    def test_parse_bounds_valid(self):
        b = UIParser.parse_bounds("[198,396][996,462]")
        assert b == (198, 396, 996, 462)

    def test_parse_bounds_invalid(self):
        assert UIParser.parse_bounds("") is None
        assert UIParser.parse_bounds("invalid_bounds") is None
        assert UIParser.parse_bounds("[10,20]") is None

    def test_compute_center(self):
        center = UIParser.compute_center((100, 200, 300, 400))
        assert center == (200, 300)

        center_odd = UIParser.compute_center((0, 0, 1080, 2400))
        assert center_odd == (540, 1200)


class TestUIParserHierarchy:
    def test_parse_complex_hierarchy(self):
        res = UIParser.parse(SAMPLE_COMPLEX_XML, clickable_only=True)
        assert res["screen"]["width"] == 1080
        assert res["screen"]["height"] == 2400
        assert res["elements_count"] > 0

        # Verify Search button is captured with content-desc
        search_elems = UIParser.find_by_text(res, "Search settings")
        assert len(search_elems) == 1
        elem = search_elems[0]
        assert elem["desc"] == "Search settings"
        assert elem["clickable"] is True
        assert elem["center"] == [990, 190]

        # Verify Network & internet is captured
        net_elems = UIParser.find_by_text(res, "Network & internet")
        assert len(net_elems) == 1
        assert net_elems[0]["center"] == [540, 360]

        # Verify switch is captured
        switches = UIParser.find_by_id(res, "airplane_switch")
        assert len(switches) == 1
        assert switches[0]["class"] == "Switch"
        assert switches[0]["center"] == [950, 640]

    def test_clickable_only_filtering(self):
        res_clickable = UIParser.parse(SAMPLE_COMPLEX_XML, clickable_only=True)
        res_all = UIParser.parse(SAMPLE_COMPLEX_XML, clickable_only=False)

        # All elements should contain separator line and container views
        assert res_all["elements_count"] >= res_clickable["elements_count"]

    def test_token_compression_ratio(self):
        """Verify token/byte compression from raw XML to parsed JSON."""
        raw_size = len(SAMPLE_COMPLEX_XML.encode("utf-8"))
        res = UIParser.parse(SAMPLE_COMPLEX_XML, clickable_only=True)
        json_size = len(json.dumps(res).encode("utf-8"))

        compression_ratio = 1.0 - (json_size / raw_size)
        assert compression_ratio > 0.40, f"Expected >40% compression, got {compression_ratio:.2%}"

    def test_malformed_xml_handling(self):
        res_empty = UIParser.parse("")
        assert res_empty["elements_count"] == 0

        res_garbage = UIParser.parse("<<<broken xml>>>")
        assert "error" in res_garbage or res_garbage["elements_count"] == 0

    def test_find_by_text_exact_and_partial(self):
        res = UIParser.parse(SAMPLE_COMPLEX_XML)
        partial = UIParser.find_by_text(res, "Network", exact=False)
        assert len(partial) == 1

        exact_fail = UIParser.find_by_text(res, "Network", exact=True)
        assert len(exact_fail) == 0

        exact_pass = UIParser.find_by_text(res, "Network & internet", exact=True)
        assert len(exact_pass) == 1
