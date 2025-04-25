<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

  <NamedLayer>
    <Name>病院名</Name>
    <UserStyle>
      <Title>病院名</Title>
      <FeatureTypeStyle>
        <Rule>
          <Name>病院名</Name>
          <Title>病院名</Title>
          <TextSymbolizer>
            <Label>
              <ogc:PropertyName>p04_002</ogc:PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-family">BIZ UDGothic</CssParameter>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>-0.15</AnchorPointX>
                  <AnchorPointY>0</AnchorPointY>
                </AnchorPoint>
              </PointPlacement>
            </LabelPlacement>
            <VendorOption name="followLine">true</VendorOption>
            <Fill>
              <CssParameter name="fill">#990099</CssParameter>
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