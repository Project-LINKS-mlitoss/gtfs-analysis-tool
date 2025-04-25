<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd" xmlns:se="http://www.opengis.net/se" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ogc="http://www.opengis.net/ogc">
  <NamedLayer>
    <se:Name>N02-22_RailroadSection</se:Name>
    <UserStyle>
      <se:Name>N02-22_RailroadSection</se:Name>
      <se:FeatureTypeStyle>
        <se:Rule>
          <se:TextSymbolizer>
            <se:Label>
              <ogc:PropertyName>n02_003</ogc:PropertyName>
            </se:Label>
            <se:Font>
              <se:SvgParameter name="font-family">UDEV Gothic Regular</se:SvgParameter>
              <se:SvgParameter name="font-size">15</se:SvgParameter>
            </se:Font>
            <se:LabelPlacement>
              <se:LinePlacement>
                <se:PerpendicularOffset>15</se:PerpendicularOffset>
                <se:GeneralizeLine>true</se:GeneralizeLine>
              </se:LinePlacement>
            </se:LabelPlacement>
            <VendorOption name="followLine">true</VendorOption>
            <se:Fill>
              <se:SvgParameter name="fill">#f05209</se:SvgParameter>
            </se:Fill>
            <se:VendorOption name="graphic-resize">stretch</se:VendorOption>
          </se:TextSymbolizer>
        </se:Rule>
      </se:FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>