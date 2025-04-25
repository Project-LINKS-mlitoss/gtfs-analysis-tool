import os
import time
import random
from xml.etree.ElementTree import Element, ElementTree as ET, SubElement, tostring

from django.conf import settings
from django.core.management.base import BaseCommand

from app.models import AppRoutes
from geo.Geoserver import Geoserver


class Command(BaseCommand):
    help = "Export バス路線 SLD rules for app_routes table"

    def add_arguments(self, parser):
        parser.add_argument("--session_id", type=str, help="Filter by session_id")
        parser.add_argument(
            "--single_color", type=bool, default=False, help="set single_color"
        )
        parser.add_argument(
            "--route_color", type=str, default="#999999", help="set route_color"
        )
        parser.add_argument(
            "--route_width", type=int, default=3, help="set route_width"
        )

    def handle(self, *args, **options):
        routes = (
            AppRoutes.objects.filter(file_name=options["session_id"])
            .values("route_id", "route_name")
            .distinct()
        )

        sld = Element(
            "StyledLayerDescriptor",
            {
                "version": "1.0.0",
                "xmlns": "http://www.opengis.net/sld",
                "xmlns:ogc": "http://www.opengis.net/ogc",
                "xmlns:xlink": "http://www.w3.org/1999/xlink",
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsi:schemaLocation": "http://www.opengis.net/sld StyledLayerDescriptor.xsd",
            },
        )

        named_layer = SubElement(sld, "NamedLayer")
        name = SubElement(named_layer, "Name")
        name.text = "Bus Route Line"

        user_style = SubElement(named_layer, "UserStyle")
        feature_type_style = SubElement(user_style, "FeatureTypeStyle")

        for route in routes:
            seed = random.randrange(1000000)
            random.seed(seed)

            rule = SubElement(feature_type_style, "Rule")

            name = SubElement(rule, "Name")
            name.text = route["route_id"]
            title = SubElement(rule, "Title")
            title.text = route["route_name"]

            filter_element = SubElement(rule, "Filter")
            property_is_equal_to = SubElement(filter_element, "PropertyIsEqualTo")
            property_name = SubElement(property_is_equal_to, "PropertyName")
            property_name.text = "route_id"
            literal = SubElement(property_is_equal_to, "Literal")
            literal.text = route["route_id"]

            line_symbolizer = SubElement(rule, "LineSymbolizer")
            stroke = SubElement(line_symbolizer, "Stroke")
            css_parameter = SubElement(stroke, "CssParameter", {"name": "stroke"})
            if options["single_color"]:
                css_parameter.text = options["route_color"]
                css_parameter = SubElement(
                    stroke, "CssParameter", {"name": "stroke-width"}
                )
                css_parameter.text = str(options["route_width"])
            else:
                css_parameter.text = self.generate_random_color()
                css_parameter = SubElement(
                    stroke, "CssParameter", {"name": "stroke-width"}
                )
                css_parameter.text = "2"
            perpendicular_offset = SubElement(line_symbolizer, "PerpendicularOffset")
            perpendicular_offset.text = "3"

            text_symbolizer = SubElement(rule, "TextSymbolizer")
            label = SubElement(text_symbolizer, "Label")
            property_name = SubElement(
                label, "{http://www.opengis.net/ogc}PropertyName"
            )
            property_name.text = "route_name"

            font = SubElement(text_symbolizer, "Font")
            css_parameter = SubElement(font, "CssParameter", {"name": "font-family"})
            css_parameter.text = "UDEV Gothic Regular"
            css_parameter = SubElement(font, "CssParameter", {"name": "font-size"})
            css_parameter.text = "14"

            fill = SubElement(text_symbolizer, "Fill")
            css_parameter = SubElement(fill, "CssParameter", {"name": "fill"})
            css_parameter.text = "#0000FF"

            label_placement = SubElement(text_symbolizer, "LabelPlacement")
            line_placement = SubElement(label_placement, "LinePlacement")
            perpendicular_offset = SubElement(line_placement, "PerpendicularOffset")
            perpendicular_offset.text = "18"
            vendor_option = SubElement(
                text_symbolizer, "VendorOption", {"name": "followLine"}
            )
            vendor_option.text = "true"

        sld_string = self.indent_formating(tostring(sld, encoding="unicode"))
        file_path = os.path.join(
            "/",
            ".media",
            options["session_id"] + "_bus_routes.sld",
        )
        with open(
            file_path,
            "w",
            encoding="utf-8",
        ) as file:
            file.write(sld_string)
        time.sleep(1)

        if os.path.exists(file_path):
            geoserver_url = "http://nginx/geoserver"
            username = settings.GEOSERVER_USER
            password = settings.GEOSERVER_PASSWORD
            geo = Geoserver(geoserver_url, username=username, password=password)
            try:
                geo.delete_style(style_name=options["session_id"] + "_bus_routes")
            except Exception as e:
                print("new style")
            geo.upload_style(path=file_path, workspace=None)

        os.remove(file_path)

    def indent_formating(self, elem):
        elem = elem.replace("><", ">\r\n<")
        return elem

    def generate_random_color(self):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        return "#{0:02x}{1:02x}{2:02x}".format(r, g, b)
