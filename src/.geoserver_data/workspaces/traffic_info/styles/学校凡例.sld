<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" 
		xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd" 
		xmlns="http://www.opengis.net/sld" 
		xmlns:ogc="http://www.opengis.net/ogc" 
		xmlns:xlink="http://www.w3.org/1999/xlink" 
		xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
		<!-- a named layer is the basic building block of an sld document -->

	<NamedLayer>
		<Name>Default Point</Name>
		<UserStyle>
			<Title>default style</Title>
			<FeatureTypeStyle>
				<Rule>
					<Name>Rule 1</Name>
					<Title>学校</Title>
					<PointSymbolizer>
						<Graphic>
							<Mark>
								<WellKnownName>circle</WellKnownName>
								<Fill>
									<CssParameter name="fill">#FFFFFF</CssParameter>
								</Fill>
                              <Stroke>
                                  <CssParameter name="stroke">#003366</CssParameter>
                                  <CssParameter name="stroke-width">2</CssParameter>
                              </Stroke>
							</Mark>
							<Size>12</Size>
						</Graphic>
					</PointSymbolizer>
				</Rule>
		    </FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>