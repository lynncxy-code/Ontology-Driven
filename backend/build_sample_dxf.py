import ezdxf
import os

def create_sample():
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()

    # Create layers
    doc.layers.add("1.21-墙体", color=3)
    doc.layers.add("1.20-柱子", color=1)

    # 1. Add some wall polylines
    points1 = [(0, 0), (1000, 0), (1000, 500), (0, 500), (0,0)]
    msp.add_lwpolyline(points1, dxfattribs={'layer': '1.21-墙体'})
    
    # 2. Add another disjoint wall using standard lines
    msp.add_line((1200, 0), (1500, 0), dxfattribs={'layer': '1.21-墙体'})
    msp.add_line((1500, 0), (1500, 300), dxfattribs={'layer': '1.21-墙体'})

    # 3. Create a block for columns
    block = doc.blocks.new(name='COLUMN_MOCKUP')
    block.add_circle((0, 0), radius=50)

    # 4. Insert the block at various locations
    msp.add_blockref('COLUMN_MOCKUP', (100, 100), dxfattribs={'layer': '1.20-柱子', 'rotation': 45})
    msp.add_blockref('COLUMN_MOCKUP', (900, 100), dxfattribs={'layer': '1.20-柱子'})
    msp.add_blockref('COLUMN_MOCKUP', (900, 400), dxfattribs={'layer': '1.20-柱子'})
    msp.add_blockref('COLUMN_MOCKUP', (100, 400), dxfattribs={'layer': '1.20-柱子'})

    # Save to frontend so the user can easily download it from browser or find it
    out_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'test_sample_factory.dxf')
    doc.saveas(out_path)
    print(f"Sample DXF created successfully at: {out_path}")

if __name__ == "__main__":
    create_sample()
