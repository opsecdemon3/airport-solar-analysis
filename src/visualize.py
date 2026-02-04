#!/usr/bin/env python3
"""
Generate interactive maps and visualizations.
"""

import folium
from folium.plugins import MarkerCluster
import os


def create_overview_map(airport_results, solar_df, output_path="output/maps/airport_solar_map.html"):
    """
    Create an interactive map of all airports with solar potential.
    
    Parameters:
    -----------
    airport_results : list
        Raw results from extract_airport_buildings
    solar_df : DataFrame
        Solar calculations from calculate_solar
    output_path : str
        Where to save the HTML map
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Center on continental US
    m = folium.Map(
        location=[39.8283, -98.5795], 
        zoom_start=4,
        tiles='cartodbpositron'
    )
    
    # Merge data
    solar_dict = solar_df.set_index('airport_code').to_dict('index')
    
    for result in airport_results:
        code = result['airport_code']
        if code not in solar_dict:
            continue
            
        solar = solar_dict[code]
        
        # Create popup HTML
        popup_html = f"""
        <div style="width: 280px;">
            <h4 style="margin: 0 0 10px 0;">{code} - {result['airport_name']}</h4>
            <hr style="margin: 5px 0;">
            
            <b>Buildings Analyzed</b><br>
            Count: {result['num_buildings']:,}<br>
            Total Roof Area: {solar['total_roof_area_sqft']:,.0f} sq ft<br>
            
            <hr style="margin: 10px 0;">
            
            <b>Solar Potential</b><br>
            Usable Roof Area: {solar['usable_area_sqft']:,.0f} sq ft<br>
            Peak Capacity: {solar['peak_capacity_mw']:.1f} MW<br>
            Annual Generation: {solar['annual_gwh']:.1f} GWh<br>
            
            <hr style="margin: 10px 0;">
            
            <b>Impact</b><br>
            Homes Equivalent: {solar['equivalent_homes']:,.0f}<br>
            CO2 Offset: {solar['co2_offset_tons']:,.0f} tons/year<br>
        </div>
        """
        
        # Color by potential
        gwh = solar['annual_gwh']
        if gwh > 500:
            color = 'darkgreen'
        elif gwh > 200:
            color = 'green'
        elif gwh > 100:
            color = 'orange'
        elif gwh > 50:
            color = 'lightred'
        else:
            color = 'red'
        
        # Size by capacity (min 8, max 25)
        radius = min(25, max(8, solar['peak_capacity_mw'] / 20))
        
        folium.CircleMarker(
            location=[result['lat'], result['lon']],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{code}: {solar['annual_gwh']:.0f} GWh/year",
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=2
        ).add_to(m)
    
    # Add legend
    legend_html = """
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; 
                background: white; padding: 10px; border-radius: 5px;
                border: 2px solid grey; font-size: 12px;">
        <b>Annual Generation Potential</b><br>
        <i style="background: darkgreen; width: 12px; height: 12px; 
           display: inline-block; border-radius: 50%;"></i> > 500 GWh<br>
        <i style="background: green; width: 12px; height: 12px; 
           display: inline-block; border-radius: 50%;"></i> 200-500 GWh<br>
        <i style="background: orange; width: 12px; height: 12px; 
           display: inline-block; border-radius: 50%;"></i> 100-200 GWh<br>
        <i style="background: #ff6666; width: 12px; height: 12px; 
           display: inline-block; border-radius: 50%;"></i> 50-100 GWh<br>
        <i style="background: red; width: 12px; height: 12px; 
           display: inline-block; border-radius: 50%;"></i> < 50 GWh<br>
        <br>
        <small>Circle size = Peak capacity</small>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add title
    title_html = """
    <div style="position: fixed; top: 10px; left: 50px; z-index: 1000;">
        <h3 style="background: white; padding: 10px; border-radius: 5px;
                   border: 2px solid grey; margin: 0;">
            🔆 Airport Area Rooftop Solar Potential
        </h3>
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))
    
    m.save(output_path)
    print(f"✓ Map saved to {output_path}")
    return m


def create_airport_detail_map(airport, buildings_gdf, solar_stats, output_dir="output/maps"):
    """
    Create a detailed map for a single airport showing building footprints.
    
    Parameters:
    -----------
    airport : dict
        Airport info (code, name, lat, lon)
    buildings_gdf : GeoDataFrame
        Building footprints near the airport
    solar_stats : dict
        Solar calculations for this airport
    output_dir : str
        Directory to save the map
    """
    os.makedirs(output_dir, exist_ok=True)
    
    m = folium.Map(
        location=[airport['lat'], airport['lon']], 
        zoom_start=12,
        tiles='cartodbpositron'
    )
    
    # Add airport marker
    folium.Marker(
        [airport['lat'], airport['lon']],
        popup=f"<b>{airport['code']}</b><br>{airport['name']}",
        icon=folium.Icon(color='red', icon='plane', prefix='fa'),
        tooltip="Airport"
    ).add_to(m)
    
    # Add building footprints if available
    if buildings_gdf is not None and len(buildings_gdf) > 0:
        # Style buildings by size
        def style_function(feature):
            area = feature['properties'].get('area_m2', 0)
            if area > 10000:  # Very large (>100k sq ft)
                color = '#1a9850'  # Dark green
            elif area > 5000:  # Large
                color = '#91cf60'  # Light green
            elif area > 2000:  # Medium
                color = '#d9ef8b'  # Yellow-green
            else:  # Small
                color = '#fee08b'  # Yellow
            
            return {
                'fillColor': color,
                'color': '#333333',
                'weight': 0.5,
                'fillOpacity': 0.6
            }
        
        folium.GeoJson(
            buildings_gdf,
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(
                fields=['area_m2'],
                aliases=['Roof Area (m²):'],
                localize=True
            )
        ).add_to(m)
    
    # Add info box
    info_html = f"""
    <div style="position: fixed; top: 10px; right: 10px; z-index: 1000;
                background: white; padding: 15px; border-radius: 5px;
                border: 2px solid grey; max-width: 250px;">
        <h4 style="margin: 0 0 10px 0;">{airport['code']} Solar Potential</h4>
        <b>Buildings:</b> {solar_stats.get('num_buildings', 0):,}<br>
        <b>Roof Area:</b> {solar_stats.get('usable_area_sqft', 0):,.0f} sq ft<br>
        <b>Peak Capacity:</b> {solar_stats.get('peak_capacity_mw', 0):.1f} MW<br>
        <b>Annual Gen:</b> {solar_stats.get('annual_gwh', 0):.1f} GWh<br>
        <b>Homes Equiv:</b> {solar_stats.get('equivalent_homes', 0):,.0f}<br>
    </div>
    """
    m.get_root().html.add_child(folium.Element(info_html))
    
    output_path = os.path.join(output_dir, f"{airport['code']}_detail.html")
    m.save(output_path)
    print(f"✓ Detail map saved to {output_path}")
    return m


if __name__ == "__main__":
    # Test with mock data
    test_results = [
        {
            'airport_code': 'ATL',
            'airport_name': 'Atlanta',
            'state': 'Georgia',
            'lat': 33.6407,
            'lon': -84.4277,
            'num_buildings': 5000,
            'total_building_area_m2': 8000000,
        },
    ]
    
    import pandas as pd
    test_df = pd.DataFrame([{
        'airport_code': 'ATL',
        'airport_name': 'Atlanta',
        'total_roof_area_sqft': 86000000,
        'usable_area_sqft': 51600000,
        'peak_capacity_mw': 960,
        'annual_gwh': 1600,
        'equivalent_homes': 152000,
        'co2_offset_tons': 640000,
    }])
    
    create_overview_map(test_results, test_df, "output/maps/test_map.html")
    print("Test map created!")
