# Textual Custom Widget Guide

## Table of Contents

1. [Custom Widget Lifecycle](#1-custom-widget-lifecycle)
2. [Combining Textual, Rich, and Plotille](#2-combining-textual-rich-and-plotille)
3. [Message System — Widget Communication](#3-message-system--widget-communication)

---

## 1. Custom Widget Lifecycle

### 1.1 Overview

Every widget in Textual follows a defined lifecycle from creation to destruction. Understanding this lifecycle is critical for building custom widgets that work correctly.

```
__init__() → compose() → _on_mount() → render() → ... → _on_unmount()
                                              ↑
                                         _on_resize()
                                         reactive changes
                                         event handlers
```

### 1.2 Step-by-Step Lifecycle

#### Step 1: `__init__()` — Construction

Called when the widget is instantiated. At this point, the widget is **not yet in the DOM** — it has no parent, no size, and cannot query other widgets.

```python
class MyWidget(Widget):
    def __init__(self, id: str, data: Any, **kwargs):
        super().__init__(id=id, **kwargs)
        # ✅ DO: Store data, initialize state
        self._data = data
        self._counter = 0

        # ❌ DON'T: Query the DOM (widget not mounted yet)
        # self.query_one("#other")  # ERROR

        # ❌ DON'T: Access self.size (not known yet)
        # width = self.size.width  # 0 or incorrect
```

**Key rules:**
- Always call `super().__init__()` first
- Store data as instance attributes
- Do NOT access `self.size` — it's not computed yet
- Do NOT query the DOM — the widget isn't mounted
- Do NOT call `mount()` or `update()` — the widget isn't attached

---

#### Step 2: `compose()` — Declare Children

Called when the widget is added to the DOM. Yield child widgets here.

```python
def compose(self) -> ComposeResult:
    yield Static("Title", id="title")
    yield Input(placeholder="Search...", id="search")
    yield SelectionList(*self._options, id="list")
```

**Key rules:**
- Yield child widgets — they will be mounted automatically
- You can access `self._data` (set in `__init__`)
- Do NOT call `self.query_one()` here — children aren't mounted yet
- Do NOT call `self.update()` on children — they don't exist yet

---

#### Step 3: `_on_mount()` — Widget is Ready

Called after the widget AND all its children are mounted. Now you can:
- Query the DOM
- Access `self.size`
- Update child widgets
- Set up reactive values

```python
def _on_mount(self, event: events.Mount) -> None:
    # ✅ Now the DOM is ready
    self.query_one("#title", Static).update("Loaded!")
    self._render_plot()  # Can access self.size now
```

**Key rules:**
- This is the right place to do initial rendering that depends on size
- You can query children and call `update()` / `mount()` / `remove_children()`
- `self.size` is now accurate

---

#### Step 4: `render()` — Custom Rendering

Override `render()` to return a **Rich renderable** for custom display. Textual calls this automatically whenever the widget needs repainting.

```python
from textual.app import RenderResult
from rich.text import Text
from rich.table import Table
from rich.panel import Panel

class MyWidget(Widget):
    def render(self) -> RenderResult:
        # Return any Rich renderable
        return Text("Hello, world!", style="bold red")

        # Or a Rich Table:
        # table = Table()
        # table.add_column("Name")
        # table.add_row("Alice")
        # return table

        # Or a Rich Panel:
        # return Panel("Content here")
```

**When does `render()` get called?**
- When the widget is first displayed
- When a `reactive` attribute changes
- When `self.refresh()` is called
- When the widget is resized (if `repaint=True`)

**Key rules:**
- Must return a Rich renderable (`Text`, `Table`, `Panel`, `Padding`, etc.)
- Do NOT call `self.query_one()` inside `render()` — it's called frequently
- Keep it fast — it runs on every repaint
- For `Static`-based widgets, use `update()` instead of overriding `render()`

---

#### Step 5: Reactives — Auto-Re-render

Reactive attributes automatically trigger `render()` when they change.

```python
from textual.reactive import reactive

class PlotWidget(Widget):
    # When these change, render() is called automatically
    plot_width = reactive(50)
    plot_height = reactive(20)
    data = reactive(None)

    def render(self) -> RenderResult:
        fig = plotille.Figure()
        fig.width = self.plot_width
        fig.height = self.plot_height
        if self.data:
            fig.scatter(self.data["x"], self.data["y"])
        return Text.from_ansi(fig.show())

    def _on_resize(self, event: events.Resize) -> None:
        # Changing reactives auto-triggers render()
        self.plot_width = max(self.size.width - 2, 20)
        self.plot_height = max(self.size.height - 2, 10)
```

**Reactive lifecycle:**
```
self.plot_width = 50       ← initial value
    ↓
render() called with 50
    ↓
self.plot_width = 80       ← new value (e.g., on resize)
    ↓
render() called with 80    ← automatic re-render
```

---

#### Step 6: `_on_resize()` — Handle Size Changes

Called when the widget's size changes (terminal resize, layout change, etc.).

```python
def _on_resize(self, event: events.Resize) -> None:
    # event.size = new Size(width, height) in character cells
    new_width = event.size.width
    new_height = event.size.height

    # Update reactives to trigger re-render
    self.plot_width = max(new_width - 2, 20)
    self.plot_height = max(new_height - 2, 10)
```

---

#### Step 7: Event Handlers — Respond to User Input

Use `@on` decorator or `on_<event>` methods.

```python
from textual import on
from textual.events import Click

class MyWidget(Widget):
    @on(Input.Changed)
    def on_search_changed(self, event: Input.Changed) -> None:
        # React to child widget events
        self._filter(event.value)

    def on_click(self, event: Click) -> None:
        # React to click on this widget
        self._handle_click(event)

    def _on_mount(self, event):
        # Lifecycle event
        pass
```

---

#### Step 8: `_on_unmount()` — Cleanup

Called when the widget is removed from the DOM.

```python
def _on_unmount(self, event: events.Unmount) -> None:
    # Cleanup: cancel timers, close resources, etc.
    pass
```

---

### 1.3 Complete Lifecycle Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    WIDGET LIFECYCLE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. __init__()                                              │
│     • Store data, set defaults                              │
│     • NO DOM access, NO size                                │
│     • Call super().__init__()                               │
│            │                                                │
│            ▼                                                │
│  2. compose()                                               │
│     • Yield child widgets                                   │
│     • Children not yet mounted                              │
│     • NO query_one(), NO update()                           │
│            │                                                │
│            ▼                                                │
│  3. _on_mount()                                             │
│     • Widget + children are in DOM                          │
│     • self.size is valid                                    │
│     • Can query, update, mount                              │
│     • Do initial rendering here                             │
│            │                                                │
│            ▼                                                │
│  4. render()  ←─── called by Textual ───→                  │
│     • Return Rich renderable                                │
│     • Triggered by: mount, reactive change, refresh()       │
│     • Keep it fast                                          │
│            │                                                │
│     ┌──────┴──────┐                                         │
│     │             │                                         │
│  5a. reactive    5b. _on_resize()                           │
│     change          • Size changed                          │
│     • Auto-         • Update reactives                     │
│       triggers         to re-render                         │
│       render()                                             │
│     │             │                                         │
│     └──────┬──────┘                                         │
│            │                                                │
│            ▼                                                │
│  6. Event handlers                                          │
│     • @on(Widget.Event)                                     │
│     • on_<event>()                                          │
│     • Can call mount(), remove_children(), update()          │
│            │                                                │
│            ▼                                                │
│  7. _on_unmount()                                           │
│     • Cleanup                                               │
│     • Cancel timers, close resources                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.4 Choosing the Right Base Class

| Base Class | Use Case | Scrollable | Key Feature |
|---|---|---|---|
| `Widget` | Fully custom rendering via `render()` | ❌ | Most control, lightest |
| `Static` | Display Rich content, update via `update()` | ❌ | Simple content display |
| `Container` | Group child widgets, custom layout | ❌ | Layout container |
| `VerticalScroll` | Scrollable vertical list of children | ✅ | Auto vertical scrollbar |
| `HorizontalScroll` | Scrollable horizontal list of children | ✅ | Auto horizontal scrollbar |
| `ScrollView` | Custom scrollable content | ✅ | Full scroll control |

### 1.5 Two Approaches to Custom Widgets

#### Approach A: Override `render()` (for self-drawn widgets)

Best when the widget draws its own content (charts, custom visuals).

```python
from textual.widget import Widget
from textual.reactive import reactive
from textual.app import RenderResult
from rich.text import Text

class PlotWidget(Widget):
    """Custom widget that renders a plotille chart."""

    plot_width = reactive(50)
    plot_height = reactive(20)

    def render(self) -> RenderResult:
        fig = plotille.Figure()
        fig.width = self.plot_width
        fig.height = self.plot_height
        # ... add data ...
        return Text.from_ansi(fig.show())

    def _on_resize(self, event):
        self.plot_width = max(self.size.width - 2, 20)
        self.plot_height = max(self.size.height - 2, 10)
```

**Pros:** Reactive auto-re-render, no manual `update()` calls, most idiomatic.
**Cons:** Must return a Rich renderable, no child widgets.

#### Approach B: Compose children + `update()` (for composite widgets)

Best when the widget contains child widgets (inputs, lists, etc.).

```python
from textual.containers import VerticalScroll
from textual.widgets import Static, Input

class GeneManagerView(VerticalScroll):
    def compose(self):
        yield Static("Query genes")
        yield Input(placeholder="Search gene")
        yield SelectionList(*self._options)

    @on(Input.Changed)
    def on_search(self, event: Input.Changed):
        # Update child widget content
        self.query_one(SelectionList).set_options(
            self._create_options(filtered_genes)
        )
```

**Pros:** Can compose complex UIs from existing widgets.
**Cons:** Must manually call `update()` / `set_options()` to refresh content.

---

## 2. Combining Textual, Rich, and Plotille

### 2.1 How They Relate

```
┌─────────────────────────────────────────────────┐
│  Textual                                        │
│  ┌───────────────────────────────────────────┐  │
│  │  Widget.render() → returns Rich renderable│  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │  Rich (rendering engine)            │  │  │
│  │  │  • Text, Table, Panel, Padding...   │  │  │
│  │  │  • Text.from_ansi() ← bridge from  │  │  │
│  │  │    ANSI strings to Rich renderables │  │  │
│  │  │  ┌───────────────────────────────┐  │  │  │
│  │  │  │  Plotille (ASCII/ANSI charts) │  │  │  │
│  │  │  │  • fig.show() → ANSI string  │  │  │  │
│  │  │  └───────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

**Key insight:** Textual uses Rich as its rendering engine. Plotille produces ANSI strings. The bridge is `Text.from_ansi()`.

### 2.2 The Data Flow

```
plotille.Figure.show()          →  str (with ANSI escape codes)
         │
         ▼
rich.text.Text.from_ansi(str)   →  Rich Text renderable
         │
         ▼
Widget.render() returns it      →  Textual displays it
   OR
Static.update(rich_text)        →  Textual displays it
```

### 2.3 Step-by-Step: Creating a Plotille Chart Widget

#### Step 1: Create the custom widget class

```python
from textual.widget import Widget
from textual.reactive import reactive
from textual.app import RenderResult
from textual.events import Resize
from rich.text import Text
import plotille
```

Choose your base class:
- `Widget` — if you only render the chart (no child widgets)
- `Container` — if you need child widgets alongside the chart
- `Static` — if you want to use `update()` instead of `render()`

#### Step 2: Define reactives for auto-re-rendering

```python
class PlotilleWidget(Widget):
    """A widget that renders a plotille scatter plot."""

    # These trigger render() automatically when changed
    plot_width = reactive(50)
    plot_height = reactive(20)
```

#### Step 3: Implement `render()` with `Text.from_ansi()`

```python
    def render(self) -> RenderResult:
        fig = plotille.Figure()
        fig.width = self.plot_width
        fig.height = self.plot_height

        # Add your data
        fig.scatter(self._x_data, self._y_data, lc="green")

        # CRITICAL: Use Text.from_ansi() to preserve colors
        return Text.from_ansi(fig.show(legend=True))
```

#### Step 4: Handle resize with `_on_resize()`

```python
    def _on_resize(self, event: Resize) -> None:
        # Update reactives → auto-triggers render()
        self.plot_width = max(self.size.width - 2, 20)
        self.plot_height = max(self.size.height - 4, 10)
```

#### Step 5: Initialize data in `__init__()` or `_on_mount()`

```python
    def __init__(self, x_data, y_data, **kwargs):
        super().__init__(**kwargs)
        # Store data (not yet rendered)
        self._x_data = x_data
        self._y_data = y_data
```

#### Step 6: Use the widget in a Screen

```python
class MainView(Screen):
    def compose(self):
        yield PlotilleWidget(
            x_data=[1, 2, 3],
            y_data=[4, 5, 6],
            id="scatter-plot"
        )
```

#### Step 7: Add CSS for proper sizing

```css
#scatter-plot {
    width: 1fr;       /* fill available horizontal space */
    height: 1fr;       /* fill available vertical space */
    text-style: bold;  /* monospace-like rendering for plotille */
}
```

### 2.4 Complete Example: PlotilleWidget

```python
from textual.widget import Widget
from textual.reactive import reactive
from textual.app import RenderResult
from textual.events import Resize
from rich.text import Text
import plotille


class PlotilleWidget(Widget):
    """A Textual widget that renders a plotille scatter plot.

    Automatically resizes when the terminal/window changes size.
    Supports ANSI colors from plotille via Rich's Text.from_ansi().
    """

    # Reactives: changing these auto-triggers render()
    plot_width = reactive(50)
    plot_height = reactive(20)

    DEFAULT_CSS = """
    PlotilleWidget {
        text-style: bold;  /* ensures monospace-like character alignment */
    }
    """

    def __init__(self, x_data, y_data, **kwargs):
        super().__init__(**kwargs)
        self._x_data = x_data
        self._y_data = y_data

    def _on_mount(self, event):
        """Set initial size based on container."""
        self.plot_width = max(self.size.width - 2, 20)
        self.plot_height = max(self.size.height - 4, 10)

    def _on_resize(self, event: Resize) -> None:
        """Re-render on resize."""
        self.plot_width = max(event.size.width - 2, 20)
        self.plot_height = max(event.size.height - 4, 10)

    def render(self) -> RenderResult:
        """Render the plotille chart as a Rich Text object."""
        fig = plotille.Figure()
        fig.width = self.plot_width
        fig.height = self.plot_height
        fig.scatter(self._x_data, self._y_data, lc="green")
        return Text.from_ansi(fig.show(legend=True))

    def update_data(self, x_data, y_data):
        """Update the chart data and re-render."""
        self._x_data = x_data
        self._y_data = y_data
        self.refresh()  # manually trigger re-render
```

### 2.5 Alternative: Using Static.update() (Composite Approach)

If you need child widgets alongside the chart (e.g., a title + chart + controls):

```python
from textual.containers import VerticalScroll
from textual.widgets import Static
from rich.text import Text
import plotille


class ScatterManagerView(VerticalScroll):
    def __init__(self, id: str, anndata, **kwargs):
        super().__init__(id=id, **kwargs)
        self._anndata = anndata

    def compose(self):
        yield Static("Scatter Plot", id="scatter-title")
        yield Static(id="scatter-plot")  # placeholder for chart

    def _on_mount(self, event):
        self._render_plot()

    def _on_resize(self, event):
        self._render_plot()

    def _render_plot(self):
        fig = plotille.Figure()
        fig.width = max(self.size.width - 2, 20)
        fig.height = max(self.size.height - 4, 10)
        # ... add data ...

        # Must use Text.from_ansi() for colors
        plot_text = Text.from_ansi(fig.show(legend=True))
        self.query_one("#scatter-plot", Static).update(plot_text)
```

### 2.6 Common Pitfalls and Solutions

| Pitfall | Symptom | Solution |
|---|---|---|
| **Raw ANSI string** | Colors show as garbled escape codes | Use `Text.from_ansi(fig.show())` instead of `fig.show()` directly |
| **Hardcoded fig size** | Chart overflows or is too small | Use `self.size.width/height` and `_on_resize()` |
| **No height constraint** | Chart expands infinitely, breaks sibling widgets | Set `height: 100%` or `height: 1fr` in CSS on the container |
| **`update()` in `compose()`** | Widget not found error | Move to `_on_mount()` — children aren't ready in `compose()` |
| **`self.size` in `__init__()`** | Returns 0 or wrong size | Use `_on_mount()` or `_on_resize()` for size-dependent logic |
| **Missing `Text.from_ansi()`** | ANSI codes corrupt other widgets' rendering | Always wrap plotille output in `Text.from_ansi()` |
| **Chart too large** | Breaks layout of other widgets | Clamp `fig.width/height` to container size, set `overflow: hidden` |

### 2.7 Rendering Pipeline: How Textual Displays Plotille

```
1. plotille.Figure.show()
   → Returns: "\x1b[32m  *\x1b[0m  ..."  (ANSI string)

2. Text.from_ansi(ansi_string)
   → Returns: Rich Text object with styled Spans
   → Each ANSI escape becomes a Rich Style

3. Widget.render() returns the Text
   → Textual's renderer converts Rich Text → Screen segments

4. Screen segments are painted to terminal
   → Colors, styles, and positioning are handled by Textual
```

### 2.8 CSS Tips for Plotille Widgets

```css
/* The chart container must have constrained dimensions */
#scatter-manager {
    width: 75%;
    height: 100%;        /* CRITICAL: prevents infinite expansion */
    overflow: hidden;    /* clip any overflow */
}

/* The plot widget itself */
PlotilleWidget {
    text-style: bold;    /* monospace alignment for plotille characters */
    padding: 0 1;        /* small horizontal padding */
    height: 100%;        /* fill container */
}

/* If using Static for the chart */
#scatter-plot {
    text-style: bold;
    height: 100%;
}
```

---

## 3. Message System — Widget Communication

### 3.1 Why Messages?

Widgets in Textual are isolated — a child widget doesn't (and shouldn't) know about its siblings. When two sibling widgets need to communicate (e.g., selecting a row in `MetadataManagerView` should update the scatter plot in `ScatterManagerView`), they use **Messages** that bubble up to a common parent, which then coordinates the action.

```
┌──────────────────────────────────────────────────────────────┐
│  Parent (Screen)                                             │
│                                                              │
│  ┌──────────────────┐              ┌──────────────────────┐  │
│  │  Widget A        │   Message   │  Widget B            │  │
│  │                   │ ──────────► │                      │  │
│  │  post_message()   │   bubbles   │  handler receives    │  │
│  │                   │   up to     │  & acts on it        │  │
│  │                   │   parent    │                      │  │
│  └──────────────────┘              └──────────────────────┘  │
│           │                                ▲                 │
│           │  1. post_message(MyMsg)        │                 │
│           ▼                                │                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Parent.on_my_msg()                                   │   │
│  │  2. event.stop()                                     │   │
│  │  3. widget_b.do_something(event.data)                │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 How Messages Work — Step by Step

#### Step 1: Define a Custom Message

A Message is a class that inherits from `textual.message.Message`. It carries data from the sender to the handler.

```python
from textual.message import Message

class MetadataManagerView(VerticalScroll):
    
    class ClusterSelected(Message):
        """Posted when a cluster row is selected in the DataTable."""
        
        def __init__(self, metadata_name: str, cluster_name: str) -> None:
            super().__init__()
            self.metadata_name = metadata_name
            self.cluster_name = cluster_name
```

**Key rules:**
- Always call `super().__init__()` — the Message base class sets up internal state (sender, time, propagation flags)
- Store your data as instance attributes
- Define the Message as a **nested class** inside the widget that sends it — this is the Textual convention and affects handler name generation

#### Step 2: Post the Message from the Sender Widget

Use `self.post_message()` to send the message. It will **bubble up** through the DOM tree (child → parent → grandparent → ...).

```python
from textual import on
from textual.widgets import DataTable

class MetadataManagerView(VerticalScroll):
    
    class ClusterSelected(Message):
        def __init__(self, metadata_name: str, cluster_name: str) -> None:
            super().__init__()
            self.metadata_name = metadata_name
            self.cluster_name = cluster_name
    
    # ... compose, etc ...
    
    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        """When user selects a row in the DataTable, post ClusterSelected."""
        row_index = event.cursor_row
        if 0 <= row_index < len(self._cluster_names):
            cluster_name = self._cluster_names[row_index]
            # Post the message — it will bubble to MainView
            self.post_message(
                self.ClusterSelected(self.selected_metadata, cluster_name)
            )
```

**What happens when `post_message()` is called:**

```
1. Message is created with data
   ClusterSelected(metadata_name="louvain", cluster_name="B cells")

2. post_message() puts it on the widget's message queue

3. Textual processes the message queue:
   a. Check if THIS widget has a handler → no (we didn't define one)
   b. Check bubble flag → True (default)
   c. Bubble to parent widget

4. Parent (Container #right-panel) receives it:
   a. Check if Container has a handler → no
   b. Bubble flag → True
   c. Bubble to its parent

5. Parent (MainView / Screen) receives it:
   a. Check if Screen has a handler → YES! on_metadata_manager_cluster_selected()
   b. Execute the handler
   c. Handler calls event.stop() → stops further bubbling
```

#### Step 3: Handle the Message in the Parent

The parent (Screen) handles the message and delegates to the target widget.

```python
from textual import on

class MainView(Screen):
    
    @on(MetadataManagerView.ClusterSelected)
    def on_metadata_manager_cluster_selected(
        self,
        event: MetadataManagerView.ClusterSelected
    ) -> None:
        """Handle cluster selection from metadata manager."""
        event.stop()  # Don't bubble further (to App)
        
        # Delegate to scatter manager
        self.scatter_manager.update_plot(
            metadata_name=event.metadata_name,
            cluster_name=event.cluster_name,
        )
```

**How is the handler name determined?**

Textual auto-generates the handler name from the Message class's qualified name:

```
Message class:  MetadataManagerView.ClusterSelected
                └─────────┘ └───────────────┘
                 namespace    class name

Handler name:   on_metadata_manager_cluster_selected
                on_ + namespace + _ + class_name (snake_case)
```

This is computed in `Message.__init_subclass__()` (see `textual/message.py:62-86`):

```python
# The qualified name is split into parts
qualname = "MetadataManagerView.ClusterSelected"
# Only last 2 parts are kept
namespace = ["MetadataManagerView", "ClusterSelected"]
# Each part is converted to snake_case and joined with _
name = "_".join(camel_to_snake(part) for part in namespace)
# Result: "metadata_manager_cluster_selected"
handler_name = f"on_{name}"
# Result: "on_metadata_manager_cluster_selected"
```

You can also use the `@on()` decorator instead of relying on the handler name:

```python
# Option A: Handler name convention (auto-generated)
def on_metadata_manager_cluster_selected(self, event): ...

# Option B: @on() decorator (explicit)
@on(MetadataManagerView.ClusterSelected)
def handle_cluster(self, event): ...
```

### 3.3 Message Bubbling — Detailed Flow

Every Message has a `bubble` class variable (default `True`). When `bubble=True`, the message travels up the DOM tree until:
- A handler calls `event.stop()` — stops further bubbling
- The message reaches the App (root) — no more parents

```
Widget Hierarchy:                    Message Bubbling Path:
                                     
App                                  ← reaches here if not stopped
 └── Screen (MainView)               ← handler here, calls event.stop()
      ├── Horizontal                  ← (skipped, not in bubble path)
      │    ├── ScatterManagerView     ← NOT in bubble path (sibling)
      │    └── Container              ← (skipped)
      │         ├── GeneManagerView   ← NOT in bubble path (sibling)
      │         └── MetadataManagerView  ← MESSAGE ORIGIN
      │              └── DataTable    ← child widget event triggers it
```

**Important:** Messages bubble **up** (child → parent → grandparent), NOT sideways to siblings. That's why the parent (Screen) must coordinate.

### 3.4 `event.stop()` — When and Why

```python
@on(MetadataManagerView.ClusterSelected)
def on_metadata_manager_cluster_selected(self, event):
    event.stop()  # ← Why?
```

| Scenario | With `event.stop()` | Without `event.stop()` |
|---|---|---|
| Message reaches Screen | Screen handles it, **stops** | Screen handles it, continues to App |
| App receives it | ❌ No | ✅ App's handler also fires (if any) |
| Performance | ✅ Slightly better | ❌ Unnecessary processing |
| Side effects | ✅ Predictable | ❌ Multiple handlers may fire |

**Rule of thumb:** Always call `event.stop()` when you've fully handled the message, unless you intentionally want parent handlers to also process it.

### 3.5 `event.prevent_default()` — Suppressing Base Class Behavior

Some messages have default actions in base classes. `prevent_default()` stops those from running:

```python
@on(Input.Submitted)
def on_search_submitted(self, event: Input.Submitted):
    event.prevent_default()  # Prevent Input's default submit behavior
    # ... custom handling ...
```

### 3.6 Non-Bubbling Messages

Some messages have `bubble=False` — they don't travel up the DOM. You must handle them on the widget itself or use `@on()` with a selector.

```python
class MyMessage(Message, bubble=False):
    """This message will NOT bubble to parent widgets."""
    pass
```

Built-in non-bubbling messages include:
- `Resize` — only the resized widget cares
- `Mount` / `Unmount` — lifecycle events
- `ScreenResume` / `ScreenSuspend` — screen-specific

### 3.7 Complete Example: MetadataManager → ScatterManager Communication

Here's the full flow from row selection to scatter plot update:

```python
# ─── metadata_manager/view.py ───

from textual import on
from textual.message import Message
from textual.containers import VerticalScroll
from textual.widgets import Static, Select, DataTable

class MetadataManagerView(VerticalScroll):
    
    # Step 1: Define the custom Message (nested class)
    class ClusterSelected(Message):
        """Posted when a cluster row is selected in the DataTable."""
        def __init__(self, metadata_name: str, cluster_name: str) -> None:
            super().__init__()
            self.metadata_name = metadata_name
            self.cluster_name = cluster_name
    
    def __init__(self, id: str, anndata, **kwargs):
        super().__init__(id=id, **kwargs)
        self._obs = anndata.obs
        self.selected_metadata = None
        self._cluster_names: list[str] = []  # maps row index → cluster name
    
    def compose(self):
        yield Static("Metadata")
        yield Select(...)
        yield DataTable(cursor_type="row", zebra_stripes=True)
    
    # Step 2: Post the message when a row is selected
    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        row_index = event.cursor_row
        if 0 <= row_index < len(self._cluster_names):
            cluster_name = self._cluster_names[row_index]
            self.post_message(
                self.ClusterSelected(self.selected_metadata, cluster_name)
            )
    
    def load_clusters(self):
        metadata = self._obs[self.selected_metadata]
        clusters = metadata.cat.categories.tolist()
        # ... populate DataTable ...
        self._cluster_names = clusters  # store for row lookup


# ─── scatter_manager/view.py ───

from textual.containers import Container
from textual.widgets import Static
from rich.text import Text
import plotille

class ScatterManagerView(Container):
    
    def __init__(self, id: str, anndata, **kwargs):
        super().__init__(id=id, **kwargs)
        self._anndata = anndata
    
    def compose(self):
        yield Static(id="scatter_plot")
    
    # Step 4: Public API for updating the plot
    def update_plot(self, metadata_name: str, cluster_name: str) -> None:
        """Re-render scatter plot for the selected cluster."""
        mask = self._anndata.obs[metadata_name] == cluster_name
        
        if "X_umap" not in self._anndata.obsm:
            self.query_one("#scatter_plot", Static).update("No UMAP data available")
            return
        
        coords = self._anndata.obsm["X_umap"]
        x = coords[mask, 0].tolist()
        y = coords[mask, 1].tolist()
        
        if not x:
            self.query_one("#scatter_plot", Static).update("No cells in cluster")
            return
        
        fig = plotille.Figure()
        fig.width = max(self.size.width - 2, 20)
        fig.height = max(self.size.height - 4, 10)
        fig.scatter(x, y, lc="green", label=cluster_name)
        
        plot_text = Text.from_ansi(fig.show(legend=True))
        self.query_one("#scatter_plot", Static).update(plot_text)


# ─── main/view.py ───

from textual import on
from textual.screen import Screen

class MainView(Screen):
    
    def __init__(self, anndata):
        super().__init__()
        self.anndata = anndata
        self.scatter_manager = None
        self.metadata_manager = None
    
    def compose(self):
        self.scatter_manager = ScatterManagerView(
            id="scatter-manager", anndata=self.anndata
        )
        self.metadata_manager = MetadataManagerView(
            id="metadata-manager", anndata=self.anndata
        )
        yield Header()
        yield Horizontal(
            self.scatter_manager,
            Container(
                GeneManagerView(id="gene-manager", anndata=self.anndata),
                self.metadata_manager,
                id="right-panel"
            ),
            id="app"
        )
    
    # Step 3: Handle the message and delegate
    @on(MetadataManagerView.ClusterSelected)
    def on_metadata_manager_cluster_selected(
        self,
        event: MetadataManagerView.ClusterSelected
    ) -> None:
        event.stop()
        self.scatter_manager.update_plot(
            metadata_name=event.metadata_name,
            cluster_name=event.cluster_name,
        )
```

### 3.8 Message Lifecycle — Complete Timeline

```
Time ──────────────────────────────────────────────────────────►

1. User clicks DataTable row
   │
   ▼
2. DataTable posts DataTable.RowSelected
   │  (internal Textual message)
   ▼
3. MetadataManagerView.on_row_selected() fires
   │  (via @on decorator)
   ▼
4. Handler calls self.post_message(ClusterSelected(...))
   │
   ▼
5. ClusterSelected is queued on MetadataManagerView's message pump
   │
   ▼
6. Textual processes the queue:
   │  a. MetadataManagerView: no handler for ClusterSelected
   │  b. bubble=True → bubble to parent (Container #right-panel)
   ▼
7. Container #right-panel: no handler → bubble to parent (Horizontal #app)
   │
   ▼
8. Horizontal #app: no handler → bubble to parent (MainView/Screen)
   │
   ▼
9. MainView: handler found! on_metadata_manager_cluster_selected()
   │  a. Execute handler body
   │  b. event.stop() called → stop propagation
   │  c. self.scatter_manager.update_plot(...) called
   ▼
10. ScatterManagerView.update_plot() executes:
    │  a. Filter anndata.obs by cluster
    │  b. Get UMAP coordinates
    │  c. Build plotille figure
    │  d. Static.update(Text.from_ansi(fig.show()))
    ▼
11. Screen repaints with updated scatter plot ✅
```

### 3.9 Alternative Communication Patterns

| Pattern | How | Best For |
|---|---|---|
| **Message bubbling** (recommended) | Child posts Message → bubbles to parent → parent delegates | Sibling communication, loose coupling |
| **Direct method call** | `self.query_one("#id", Widget).method()` | Parent→child, simple cases |
| **Reactive on Screen** | Screen has reactive, children bind to it | Shared state across many widgets |
| **App-level store** | `self.app.shared_state` | Global state, last resort |

### 3.10 Common Pitfalls with Messages

| Pitfall | Symptom | Solution |
|---|---|---|
| **Forgot `super().__init__()`** in Message | `AttributeError` or message not delivered | Always call `super().__init__()` in Message `__init__` |
| **Message defined outside widget class** | Handler name doesn't include widget namespace | Define Message as nested class inside the sending widget |
| **Forgot `event.stop()`** | Handler fires multiple times (Screen + App) | Call `event.stop()` when you've handled the message |
| **Posting from `compose()`** | Message lost (widget not mounted yet) | Only post messages after `_on_mount()` |
| **Trying to send to sibling directly** | Message never arrives | Messages bubble UP only; parent must coordinate |
| **Handler name mismatch** | Handler never fires | Use `@on(MessageClass)` decorator for explicit binding |
| **`bubble=False` message** | Parent never receives it | Handle on the widget itself, or set `bubble=True` |
