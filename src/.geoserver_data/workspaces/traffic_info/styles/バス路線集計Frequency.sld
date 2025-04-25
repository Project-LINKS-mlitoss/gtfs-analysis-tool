<?xml version="1.0" encoding="ISO-8859-1"?>
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
          <Title>1 - 9</Title>
          <ogc:Filter>
            <ogc:PropertyIsBetween>
              <ogc:PropertyName>frequency</ogc:PropertyName>
              <ogc:LowerBoundary>
                <ogc:Literal>1</ogc:Literal>
              </ogc:LowerBoundary>
              <ogc:UpperBoundary>
                <ogc:Literal>9</ogc:Literal>
              </ogc:UpperBoundary>
            </ogc:PropertyIsBetween>
          </ogc:Filter>
          <TextSymbolizer>
            <Label>
              <ogc:PropertyName>frequency</ogc:PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-family">UDEV Gothic Regular</CssParameter>
              <CssParameter name="font-size">15</CssParameter>
            </Font>
            <VendorOption name="followLine">true</VendorOption>
            <LabelPlacement>
              <LinePlacement>
                <PerpendicularOffset>
                  -20
                </PerpendicularOffset>
              </LinePlacement>
            </LabelPlacement>
            <Fill>
              <CssParameter name="fill">#00af20</CssParameter>
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
          <Title>10 - 29</Title>
          <ogc:Filter>
            <ogc:PropertyIsBetween>
              <ogc:PropertyName>frequency</ogc:PropertyName>
              <ogc:LowerBoundary>
                <ogc:Literal>10</ogc:Literal>
              </ogc:LowerBoundary>
              <ogc:UpperBoundary>
                <ogc:Literal>29</ogc:Literal>
              </ogc:UpperBoundary>
            </ogc:PropertyIsBetween>
          </ogc:Filter>
          <TextSymbolizer>
            <Label>
              <ogc:PropertyName>frequency</ogc:PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-family">UDEV Gothic Regular</CssParameter>
              <CssParameter name="font-size">15</CssParameter>
            </Font>
            <VendorOption name="followLine">true</VendorOption>
            <LabelPlacement>
              <LinePlacement>
                <PerpendicularOffset>
                  -20
                </PerpendicularOffset>
              </LinePlacement>
            </LabelPlacement>
            <Fill>
              <CssParameter name="fill">#00af20</CssParameter>
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
          <Title>30 -</Title>
          <ogc:Filter>
            <ogc:PropertyIsBetween>
              <ogc:PropertyName>frequency</ogc:PropertyName>
              <ogc:LowerBoundary>
                <ogc:Literal>30</ogc:Literal>
              </ogc:LowerBoundary>
              <ogc:UpperBoundary>
                <ogc:Literal>9999</ogc:Literal>
              </ogc:UpperBoundary>
            </ogc:PropertyIsBetween>
          </ogc:Filter>
          <TextSymbolizer>
            <Label>
              <ogc:PropertyName>frequency</ogc:PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-family">UDEV Gothic Regular</CssParameter>
              <CssParameter name="font-size">15</CssParameter>
            </Font>
            <VendorOption name="followLine">true</VendorOption>
            <LabelPlacement>
              <LinePlacement>
                <PerpendicularOffset>
                  -20
                </PerpendicularOffset>
              </LinePlacement>
            </LabelPlacement>
            <Fill>
              <CssParameter name="fill">#00af20</CssParameter>
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