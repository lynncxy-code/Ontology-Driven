import ezdxf

def main():
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Create layers
    doc.layers.add('1.21-墙体')
    doc.layers.add('1.20-柱子')

    # Draw an L-shaped warehouse with corners
    wall_points = [
        (0, 0),             # 1. 坐下角
        (10000, 0),         # 2. 右下角
        (10000, 5000),      # 3. 右上偏下
        (6000, 5000),       # 4. 内凹转角处 (转折点)
        (6000, 8000),       # 5. 内凹向上
        (4000, 8000),       # 6. 继续曲折
        (4000, 10000),      # 7. 最顶部
        (0, 10000),         # 8. 左上角
        (0, 0)              # 回合
    ]
    msp.add_lwpolyline(wall_points, dxfattribs={'layer': '1.21-墙体'})

    # 另外在内部加一个小隔间（例如库房办公室），不闭合或闭合均可
    office_points = [
        (0, 3000),
        (3000, 3000),
        (3000, 0)
    ]
    msp.add_lwpolyline(office_points, dxfattribs={'layer': '1.21-墙体'})

    # Insert columns (blocks)
    block = doc.blocks.new(name='SM_Pole_01')
    # 给图块添加一个圆，半径200，让其在CAD里现形
    block.add_circle(center=(0, 0), radius=200, dxfattribs={'layer': '1.20-柱子'})
    
    # 墙角立柱 (只保留角落的柱子)
    col_points = [
        (200, 200),       # 1. 左下角
        (9800, 200),      # 2. 右下角
        (9800, 4800),     # 3. 右上偏下
        (6200, 4800),     # 4. 内凹转角处 (转折点)
        (6200, 7800),     # 5. 内凹向上
        (3800, 7800),     # 6. 继续曲折
        (3800, 9800),     # 7. 最顶部
        (200, 9800)       # 8. 左上角
    ]
    
    for pt in col_points:
        msp.add_blockref('SM_Pole_01', insert=pt, dxfattribs={'layer': '1.20-柱子'})

    doc.saveas('demo_warehouse_10m_v3.dxf')
    print("Created demo_warehouse_10m_v3.dxf successfully!")

if __name__ == "__main__":
    main()
