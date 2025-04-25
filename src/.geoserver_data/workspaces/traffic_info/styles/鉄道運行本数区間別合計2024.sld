<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0"
                       xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd"
                       xmlns="http://www.opengis.net/sld"
                       xmlns:ogc="http://www.opengis.net/ogc"
                       xmlns:xlink="http://www.w3.org/1999/xlink"
                       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

  <NamedLayer>
    <Name>Aggregator Line</Name>
    <UserStyle>
      <Title>Aggregator Line</Title>
      <FeatureTypeStyle>
        <Rule>
          <Name>1 - 9</Name>
          <Title>1～9本</Title>
          <ogc:Filter>
            <ogc:PropertyIsBetween>
              <ogc:PropertyName>運行本数</ogc:PropertyName>
              <ogc:LowerBoundary>
                <ogc:Literal>1</ogc:Literal>
              </ogc:LowerBoundary>
              <ogc:UpperBoundary>
                <ogc:Literal>9</ogc:Literal>
              </ogc:UpperBoundary>
            </ogc:PropertyIsBetween>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#e01e5a</CssParameter>
              <CssParameter name="stroke-width">1</CssParameter>
            </Stroke>
            <PerpendicularOffset>0</PerpendicularOffset>
          </LineSymbolizer>
          <TextSymbolizer>
            <Label>
              <ogc:PropertyName>運行本数</ogc:PropertyName>
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
              <CssParameter name="fill">#e01e5a</CssParameter>
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
          <Name>10 - 29</Name>
          <Title>10～29本</Title>
          <ogc:Filter>
            <ogc:PropertyIsBetween>
              <ogc:PropertyName>運行本数</ogc:PropertyName>
              <ogc:LowerBoundary>
                <ogc:Literal>10</ogc:Literal>
              </ogc:LowerBoundary>
              <ogc:UpperBoundary>
                <ogc:Literal>29</ogc:Literal>
              </ogc:UpperBoundary>
            </ogc:PropertyIsBetween>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#e01e5a</CssParameter>
              <CssParameter name="stroke-width">4</CssParameter>
            </Stroke>
            <PerpendicularOffset>0</PerpendicularOffset>
          </LineSymbolizer>
          <TextSymbolizer>
            <Label>
              <ogc:PropertyName>運行本数</ogc:PropertyName>
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
              <CssParameter name="fill">#e01e5a</CssParameter>
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
          <Name>30 -</Name>
          <Title>30本以上</Title>
          <ogc:Filter>
            <ogc:PropertyIsBetween>
              <ogc:PropertyName>運行本数</ogc:PropertyName>
              <ogc:LowerBoundary>
                <ogc:Literal>30</ogc:Literal>
              </ogc:LowerBoundary>
              <ogc:UpperBoundary>
                <ogc:Literal>9999</ogc:Literal>
              </ogc:UpperBoundary>
            </ogc:PropertyIsBetween>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#e01e5a</CssParameter>
              <CssParameter name="stroke-width">7</CssParameter>
            </Stroke>
            <PerpendicularOffset>0</PerpendicularOffset>
          </LineSymbolizer>
          <TextSymbolizer>
            <Label>
              <ogc:PropertyName>運行本数</ogc:PropertyName>
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
              <CssParameter name="fill">#e01e5a</CssParameter>
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