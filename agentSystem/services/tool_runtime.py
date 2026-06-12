class ToolRuntime:
    def __init__(self):
        self.loaded_tools = {}

    def load_from_db(self, tools):
        for t in tools:
            exec(t.code, {}, self.loaded_tools)

    def call(self, name, **kwargs):
        if name not in self.loaded_tools:
            raise Exception("Tool not found at runtime.")
        return self.loaded_tools[name](**kwargs)

tool_runtime = ToolRuntime()
