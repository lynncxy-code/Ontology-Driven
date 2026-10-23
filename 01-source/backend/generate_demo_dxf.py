import ezdxf

def main():
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Create layers
    doc.layers.add('1.21-墙体')
    doc.layers.add('1.20-柱子')

    # Draw 4000x4000 room walls
    # Origin at (0,0) to (4000, 4000)
    wall_points = [
        (0, 0),
        (4000, 0),
        (4000, 4000),
        (0, 4000),
        (0, 0) # close loop
    ]
    msp.add_lwpolyline(wall_points, dxfattribs={'layer': '1.21-墙体'})

    # Insert columns (blocks)
    # Define a block named 'SM_Pole_01'
    block = doc.blocks.new(name='SM_Pole_01')
    
    # Insert columns near corners (inset by 200mm)
    col_points = [
        (200, 200),
        (3800, 200),
        (3800, 3800),
        (200, 3800)
    ]
    
    for pt in col_points:
        msp.add_blockref('SM_Pole_01', insert=pt, dxfattribs={'layer': '1.20-柱子'})

    doc.saveas('demo_room_4m.dxf')
    print("Created demo_room_4m.dxf successfully!")

if __name__ == "__main__":
    main()
