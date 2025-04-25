<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" 
        xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd" 
        xmlns="http://www.opengis.net/sld" 
        xmlns:ogc="http://www.opengis.net/ogc" 
        xmlns:xlink="http://www.w3.org/1999/xlink" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <NamedLayer>
        <Name>Blue arrows</Name>
        <UserStyle>
            <Title>運行方向</Title>
            <FeatureTypeStyle>
                <Rule>
                    <Name>運行方向</Name>
                    <LineSymbolizer>
                        <Stroke>
                            <CssParameter name="stroke">#e01e5a</CssParameter>
                            <CssParameter name="stroke-width">2</CssParameter>
                        </Stroke>
                    </LineSymbolizer>
                    <PointSymbolizer>
                        <Geometry>
                            <ogc:Function name="endPoint">
                                <ogc:PropertyName>geom</ogc:PropertyName>
                            </ogc:Function>
                        </Geometry>
                        <Graphic>
                            <Mark>
                                <WellKnownName>shape://oarrow</WellKnownName>
                                <Fill>
                                <CssParameter name="fill">#e01e5a</CssParameter>
                                <CssParameter name="fill-opacity">1.0</CssParameter>
                                </Fill>
                                <Stroke>
                                    <CssParameter name="stroke">#e01e5a</CssParameter>
                                    <CssParameter name="stroke-width">1</CssParameter>
                                </Stroke>
                            </Mark>
                            <Size>27</Size>
                            <Rotation>
                                <ogc:Function name="endAngle">
                                    <ogc:PropertyName>geom</ogc:PropertyName>
                                </ogc:Function>
                            </Rotation>
                        </Graphic>
                    </PointSymbolizer>
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