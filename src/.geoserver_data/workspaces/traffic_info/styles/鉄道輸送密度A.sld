<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0"
                       xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd"
                       xmlns="http://www.opengis.net/sld"
                       xmlns:ogc="http://www.opengis.net/ogc"
                       xmlns:xlink="http://www.w3.org/1999/xlink"
                       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

  <NamedLayer>
    <Name>鉄道輸送密度</Name>
    <UserStyle>
      <Title>鉄道輸送密度</Title>
      <FeatureTypeStyle>
        <Rule>
          <Name>0</Name>
          <Title>0人 もしくは欠測値</Title>
          <ogc:Filter>
            <ogc:PropertyIsLessThanOrEqualTo>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:Literal>0</ogc:Literal>
            </ogc:PropertyIsLessThanOrEqualTo>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">3</CssParameter>
            </Stroke>
            <PerpendicularOffset>0</PerpendicularOffset>
          </LineSymbolizer>
          <TextSymbolizer>
            <Label>
              <ogc:PropertyName>集計値</ogc:PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-family">UDEV Gothic Regular</CssParameter>
              <CssParameter name="font-size">15</CssParameter>
            </Font>
            <VendorOption name="followLine">true</VendorOption>
            <LabelPlacement>
              <LinePlacement>
                <PerpendicularOffset>
                  20
                </PerpendicularOffset>
              </LinePlacement>
            </LabelPlacement>
            <Fill>
              <CssParameter name="fill">#888888</CssParameter>
            </Fill>
            <Halo>
              <Radius>1</Radius>
              <Fill>
                <CssParameter name="fill">#FFFFFF</CssParameter>
              </Fill>
            </Halo>
          </TextSymbolizer>
        </Rule>
        <Rule>
          <Name>1 - 100</Name>
          <Title>1～100人</Title>
          <ogc:Filter>
            <ogc:PropertyIsBetween>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:LowerBoundary>
                <ogc:Literal>1</ogc:Literal>
              </ogc:LowerBoundary>
              <ogc:UpperBoundary>
                <ogc:Literal>100</ogc:Literal>
              </ogc:UpperBoundary>
            </ogc:PropertyIsBetween>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#712ca1</CssParameter>
              <CssParameter name="stroke-width">3</CssParameter>
            </Stroke>
            <PerpendicularOffset>0</PerpendicularOffset>
          </LineSymbolizer>
          <TextSymbolizer>
            <Label>
              <ogc:PropertyName>集計値</ogc:PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-family">UDEV Gothic Regular</CssParameter>
              <CssParameter name="font-size">15</CssParameter>
            </Font>
            <VendorOption name="followLine">true</VendorOption>
            <LabelPlacement>
              <LinePlacement>
                <PerpendicularOffset>
                  20
                </PerpendicularOffset>
              </LinePlacement>
            </LabelPlacement>
            <Fill>
              <CssParameter name="fill">#888888</CssParameter>
            </Fill>
            <Halo>
              <Radius>1</Radius>
              <Fill>
                <CssParameter name="fill">#FFFFFF</CssParameter>
              </Fill>
            </Halo>
          </TextSymbolizer>
        </Rule>
        <Rule>
          <Name>101 - 1000</Name>
          <Title>101～1,000人</Title>
          <ogc:Filter>
            <ogc:PropertyIsBetween>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:LowerBoundary>
                <ogc:Literal>101</ogc:Literal>
              </ogc:LowerBoundary>
              <ogc:UpperBoundary>
                <ogc:Literal>1000</ogc:Literal>
              </ogc:UpperBoundary>
            </ogc:PropertyIsBetween>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#2d869d</CssParameter>
              <CssParameter name="stroke-width">3</CssParameter>
            </Stroke>
            <PerpendicularOffset>0</PerpendicularOffset>
          </LineSymbolizer>
          <TextSymbolizer>
            <Label>
              <ogc:PropertyName>集計値</ogc:PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-family">UDEV Gothic Regular</CssParameter>
              <CssParameter name="font-size">15</CssParameter>
            </Font>
            <VendorOption name="followLine">true</VendorOption>
            <LabelPlacement>
              <LinePlacement>
                <PerpendicularOffset>
                  20
                </PerpendicularOffset>
              </LinePlacement>
            </LabelPlacement>
            <Fill>
              <CssParameter name="fill">#888888</CssParameter>
            </Fill>
            <Halo>
              <Radius>1</Radius>
              <Fill>
                <CssParameter name="fill">#FFFFFF</CssParameter>
              </Fill>
            </Halo>
          </TextSymbolizer>
        </Rule>
        <Rule>
          <Name>1001 - 10000</Name>
          <Title>1,001～10,000人</Title>
          <ogc:Filter>
            <ogc:PropertyIsBetween>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:LowerBoundary>
                <ogc:Literal>1001</ogc:Literal>
              </ogc:LowerBoundary>
              <ogc:UpperBoundary>
                <ogc:Literal>10000</ogc:Literal>
              </ogc:UpperBoundary>
            </ogc:PropertyIsBetween>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#00b2f0</CssParameter>
              <CssParameter name="stroke-width">3</CssParameter>
            </Stroke>
            <PerpendicularOffset>0</PerpendicularOffset>
          </LineSymbolizer>
          <TextSymbolizer>
            <Label>
              <ogc:PropertyName>集計値</ogc:PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-family">UDEV Gothic Regular</CssParameter>
              <CssParameter name="font-size">15</CssParameter>
            </Font>
            <VendorOption name="followLine">true</VendorOption>
            <LabelPlacement>
              <LinePlacement>
                <PerpendicularOffset>
                  20
                </PerpendicularOffset>
              </LinePlacement>
            </LabelPlacement>
            <Fill>
              <CssParameter name="fill">#888888</CssParameter>
            </Fill>
            <Halo>
              <Radius>1</Radius>
              <Fill>
                <CssParameter name="fill">#FFFFFF</CssParameter>
              </Fill>
            </Halo>
          </TextSymbolizer>
        </Rule>
        <Rule>
          <Name>10001 - 100000</Name>
          <Title>10,001～100,000人</Title>
          <ogc:Filter>
            <ogc:PropertyIsBetween>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:LowerBoundary>
                <ogc:Literal>10001</ogc:Literal>
              </ogc:LowerBoundary>
              <ogc:UpperBoundary>
                <ogc:Literal>100000</ogc:Literal>
              </ogc:UpperBoundary>
            </ogc:PropertyIsBetween>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#93d14f</CssParameter>
              <CssParameter name="stroke-width">3</CssParameter>
            </Stroke>
            <PerpendicularOffset>0</PerpendicularOffset>
          </LineSymbolizer>
          <TextSymbolizer>
            <Label>
              <ogc:PropertyName>集計値</ogc:PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-family">UDEV Gothic Regular</CssParameter>
              <CssParameter name="font-size">15</CssParameter>
            </Font>
            <VendorOption name="followLine">true</VendorOption>
            <LabelPlacement>
              <LinePlacement>
                <PerpendicularOffset>
                  20
                </PerpendicularOffset>
              </LinePlacement>
            </LabelPlacement>
            <Fill>
              <CssParameter name="fill">#888888</CssParameter>
            </Fill>
            <Halo>
              <Radius>1</Radius>
              <Fill>
                <CssParameter name="fill">#FFFFFF</CssParameter>
              </Fill>
            </Halo>
          </TextSymbolizer>
        </Rule>
        <Rule>
          <Name>100001 - 500000</Name>
          <Title>100,001～500,000人</Title>
          <ogc:Filter>
            <ogc:PropertyIsBetween>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:LowerBoundary>
                <ogc:Literal>100001</ogc:Literal>
              </ogc:LowerBoundary>
              <ogc:UpperBoundary>
                <ogc:Literal>500000</ogc:Literal>
              </ogc:UpperBoundary>
            </ogc:PropertyIsBetween>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#ffc100</CssParameter>
              <CssParameter name="stroke-width">3</CssParameter>
            </Stroke>
            <PerpendicularOffset>0</PerpendicularOffset>
          </LineSymbolizer>
          <TextSymbolizer>
            <Label>
              <ogc:PropertyName>集計値</ogc:PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-family">UDEV Gothic Regular</CssParameter>
              <CssParameter name="font-size">15</CssParameter>
            </Font>
            <VendorOption name="followLine">true</VendorOption>
            <LabelPlacement>
              <LinePlacement>
                <PerpendicularOffset>
                  20
                </PerpendicularOffset>
              </LinePlacement>
            </LabelPlacement>
            <Fill>
              <CssParameter name="fill">#888888</CssParameter>
            </Fill>
            <Halo>
              <Radius>1</Radius>
              <Fill>
                <CssParameter name="fill">#FFFFFF</CssParameter>
              </Fill>
            </Halo>
          </TextSymbolizer>
        </Rule>
        <Rule>
          <Name>500001 -</Name>
          <Title>500,001人以上</Title>
          <ogc:Filter>
            <ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyName>集計値</ogc:PropertyName>
              <ogc:Literal>500001</ogc:Literal>
            </ogc:PropertyIsGreaterThanOrEqualTo>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#FF0000</CssParameter>
              <CssParameter name="stroke-width">3</CssParameter>
            </Stroke>
            <PerpendicularOffset>0</PerpendicularOffset>
          </LineSymbolizer>
          <TextSymbolizer>
            <Label>
              <ogc:PropertyName>集計値</ogc:PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-family">UDEV Gothic Regular</CssParameter>
              <CssParameter name="font-size">15</CssParameter>
            </Font>
            <VendorOption name="followLine">true</VendorOption>
            <LabelPlacement>
              <LinePlacement>
                <PerpendicularOffset>
                  20
                </PerpendicularOffset>
              </LinePlacement>
            </LabelPlacement>
            <Fill>
              <CssParameter name="fill">#888888</CssParameter>
            </Fill>
            <Halo>
              <Radius>1</Radius>
              <Fill>
                <CssParameter name="fill">#FFFFFF</CssParameter>
              </Fill>
            </Halo>
          </TextSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>