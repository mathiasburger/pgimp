class Layer:
    def __init__(self, properties: dict) -> None:
        super().__init__()
        self.name = properties['name']
        self.visible = properties['visible']
        self.opacity = float(properties['opacity'])
        self.position = properties['position']
