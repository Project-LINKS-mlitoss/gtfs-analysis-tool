<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" 
        xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd" 
        xmlns="http://www.opengis.net/sld" 
        xmlns:ogc="http://www.opengis.net/ogc" 
        xmlns:xlink="http://www.w3.org/1999/xlink" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <NamedLayer>
        <Name>到達地点</Name>
        <UserStyle>
            <Title>到達地点</Title>
            <FeatureTypeStyle>
                <Rule>
                    <Name>到達地点</Name>
                    <PointSymbolizer>
                      <Graphic>
                        <ExternalGraphic>
                          <OnlineResource xlink:type="simple" xlink:href="arrival.png" />
                          <Format>image/png</Format>
                        </ExternalGraphic>
                        <Size>20</Size>
                      </Graphic>
                    </PointSymbolizer>
                </Rule>
            </FeatureTypeStyle>
        </UserStyle>
    </NamedLayer>
</StyledLayerDescriptor>