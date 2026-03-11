import time

class SharedState:
    def __init__(self):
        # I3DSpatial
        self.translation_x = 0.0
        self.translation_y = 0.0
        self.translation_z = 0.0
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.rotation_z = 0.0
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.scale_z = 1.0
        
        # I3DVisual
        self.material_variant = "normal"
        self.is_visible = True
        
        # I3DBehavior
        self.animation_state = "idle"
        self.fx_trigger = ""
        self.ui_label_content = "Aircraft-001 Ready"
        
        self.asset_id = "aircraft_001"
        self.timestamp = time.time()

    def update(self, data):
        valid_keys = [
            'translation_x', 'translation_y', 'translation_z',
            'rotation_x', 'rotation_y', 'rotation_z',
            'scale_x', 'scale_y', 'scale_z',
            'material_variant', 'is_visible',
            'animation_state', 'fx_trigger', 'ui_label_content'
        ]
        for key in valid_keys:
            if key in data:
                setattr(self, key, data[key])
        self.timestamp = time.time()

    def to_dict(self):
        return self.__dict__
