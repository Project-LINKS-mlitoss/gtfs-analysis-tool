<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ogc="http://www.opengis.net/ogc" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1.0" xmlns:se="http://www.opengis.net/se">
  <NamedLayer>
    <se:Name>利用交通手段_総数</se:Name>
    <UserStyle>

      <se:FeatureTypeStyle>
        <se:Rule>
          <se:Name>0人</se:Name>
          <se:Description>
            <se:Title>0人</se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
              <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:Literal>0</ogc:Literal>
              </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <se:PolygonSymbolizer>
          <se:Fill>
            <se:SvgParameter name="fill">#FFFFFF</se:SvgParameter>
          </se:Fill>
          <se:Stroke>
            <se:SvgParameter name="stroke">#807f7f</se:SvgParameter>
            <se:SvgParameter name="stroke-width">0.3</se:SvgParameter>
            <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
          </se:Stroke>
          </se:PolygonSymbolizer>
        </se:Rule>
        <se:Rule>
          <se:Name>1 - 200人</se:Name>
          <se:Description>
            <se:Title>1～200人</se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
            <ogc:And>
              <ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:Literal>1</ogc:Literal>
              </ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyIsLessThanOrEqualTo>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:Literal>200</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <se:PolygonSymbolizer>
          <se:Fill>
            <se:SvgParameter name="fill">#FFE3E0</se:SvgParameter>
          </se:Fill>
          <se:Stroke>
            <se:SvgParameter name="stroke">#807f7f</se:SvgParameter>
            <se:SvgParameter name="stroke-width">0.3</se:SvgParameter>
            <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
          </se:Stroke>
          </se:PolygonSymbolizer>
        </se:Rule>
        <se:Rule>
          <se:Name>201 - 500人</se:Name>
          <se:Description>
            <se:Title>201～500人</se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
            <ogc:And>
              <ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:Literal>201</ogc:Literal>
              </ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyIsLessThanOrEqualTo>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:Literal>500</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <se:PolygonSymbolizer>
          <se:Fill>
            <se:SvgParameter name="fill">#FED5A2</se:SvgParameter>
          </se:Fill>
          <se:Stroke>
            <se:SvgParameter name="stroke">#807f7f</se:SvgParameter>
            <se:SvgParameter name="stroke-width">0.3</se:SvgParameter>
            <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
          </se:Stroke>
          </se:PolygonSymbolizer>
        </se:Rule>
        <se:Rule>
          <se:Name>501 - 800人</se:Name>
          <se:Description>
            <se:Title>501～800人</se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
            <ogc:And>
              <ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:Literal>501</ogc:Literal>
              </ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyIsLessThanOrEqualTo>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:Literal>800</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <se:PolygonSymbolizer>
          <se:Fill>
            <se:SvgParameter name="fill">#FEB2A2</se:SvgParameter>
          </se:Fill>
          <se:Stroke>
            <se:SvgParameter name="stroke">#807f7f</se:SvgParameter>
            <se:SvgParameter name="stroke-width">0.3</se:SvgParameter>
            <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
          </se:Stroke>
          </se:PolygonSymbolizer>
        </se:Rule>
        <se:Rule>
          <se:Name>801 - 1000人</se:Name>
          <se:Description>
            <se:Title>801～1,000人</se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
            <ogc:And>
              <ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:Literal>801</ogc:Literal>
              </ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyIsLessThanOrEqualTo>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:Literal>1000</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <se:PolygonSymbolizer>
          <se:Fill>
            <se:SvgParameter name="fill">#FEA2A2</se:SvgParameter>
          </se:Fill>
          <se:Stroke>
            <se:SvgParameter name="stroke">#807f7f</se:SvgParameter>
            <se:SvgParameter name="stroke-width">0.3</se:SvgParameter>
            <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
          </se:Stroke>
          </se:PolygonSymbolizer>
        </se:Rule>
        <se:Rule>
          <se:Name>1001 - 3000人</se:Name>
          <se:Description>
            <se:Title>1,001～3,000人</se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
            <ogc:And>
              <ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:Literal>1001</ogc:Literal>
              </ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyIsLessThanOrEqualTo>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:Literal>3000</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <se:PolygonSymbolizer>
          <se:Fill>
            <se:SvgParameter name="fill">#FE808B</se:SvgParameter>
          </se:Fill>
          <se:Stroke>
            <se:SvgParameter name="stroke">#807f7f</se:SvgParameter>
            <se:SvgParameter name="stroke-width">0.3</se:SvgParameter>
            <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
          </se:Stroke>
          </se:PolygonSymbolizer>
        </se:Rule>
                <se:Rule>
          <se:Name>3001 - 6000人</se:Name>
          <se:Description>
            <se:Title>3,001～6,000人</se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
            <ogc:And>
              <ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:Literal>3001</ogc:Literal>
              </ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyIsLessThanOrEqualTo>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:Literal>6000</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <se:PolygonSymbolizer>
          <se:Fill>
            <se:SvgParameter name="fill">#F23F42</se:SvgParameter>
          </se:Fill>
          <se:Stroke>
            <se:SvgParameter name="stroke">#807f7f</se:SvgParameter>
            <se:SvgParameter name="stroke-width">0.3</se:SvgParameter>
            <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
          </se:Stroke>
          </se:PolygonSymbolizer>
        </se:Rule>
        <se:Rule>
          <se:Name>6001人以上</se:Name>
          <se:Description>
            <se:Title>6,001人以上</se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
              <ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:Literal>6001</ogc:Literal>
              </ogc:PropertyIsGreaterThanOrEqualTo>
          </ogc:Filter>
          <se:PolygonSymbolizer>
          <se:Fill>
            <se:SvgParameter name="fill">#FF0000</se:SvgParameter>
          </se:Fill>
          <se:Stroke>
            <se:SvgParameter name="stroke">#807f7f</se:SvgParameter>
            <se:SvgParameter name="stroke-width">0.3</se:SvgParameter>
            <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
          </se:Stroke>
          </se:PolygonSymbolizer>
        </se:Rule>
      </se:FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>