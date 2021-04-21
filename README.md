# propixx_flicker

This module provides tools to show frequency-tagged stimuli in Psychopy using a Propixx projector.
These tools make it easy to show stimuli that flicker at frequencies up to the 720 Hz.


# Background

The [Propixx projector](https://vpixx.com/products/propixx/) allows you to show stimuli in greyscale at a refresh rate of 1440 Hz.
Here's how that works.
The stimulus-presentation computer sends frames to the projector at 120 Hz.
For every screen refresh you send to the projector, the projector shows 12 frames.
Images from the stimulus computer are split into 4 quadrants, and information from each RGB channel is treated as a separate image.
Your single image will be displayed like this: Red Q1, Red Q2, Red Q3, Red Q4, Green Q1, Green Q2...

Quadrants of the screen are organized like this:
```
      1  2
      3  4
```

Frames are selected like this:
```
for color_channel in (red, green, blue):
    for quadrant in range(4):
        show_data(quadrant, color_channel)
```

The tools in `propixx_flicker` make it easy to show flickering stimuli on a Propixx projector without worrying about any of this.

This high-frequency refresh rate helps to [measure cortical excitability using rapid frequency tagging](https://doi.org/10.1016/j.neuroimage.2019.03.056).


# Classes

This module provides three main classes.

## `QuadStim`
Show a non-flickering stimulus on the Propixx projector. This takes a single Psychopy stimulus object and duplicates it across the four quadrants of the screen.

## `OpacityFlickerStim`
Flicker a Psychopy stimulus object by modulating the opacity of the image.

## `BrightnessFlickerStim`
Flicker a Psychopy stimulus object by modulating the brightness of the image.


# Extensibility

The classes currently support sinusoidal flickering, but can easily be overridden to show other kinds of flickers.
To do that, you would overwrite the `_next()` method.
For example, if you want your stimuli to flicker with a square wave, you could make a new class that inherits from `OpacityFlickerStim` or `BrightnessFlickerStim`.

```python
class SquareFlickerStim(BrightnessFlickerStim):
    def _next(self):
        self.phase += self._freq # Update the phase
        self.phase = np.mod(self.phase, 2 * np.pi) # wrap to 2pi
        # Square-wave modulation
        if self.phase <= np.pi:
            opacity = 1.0
        else:
            opacity = 0.0
        return opacity
```


# Example

See `minimal_example.py` for an example of how to use this module.


# Requirements

* [Psychopy 3](https://www.psychopy.org/download.html)
* [Propixx projector](https://vpixx.com/products/propixx/)
* Matlab and the Datapixx toolbox provided by VPixx. (This is necessary to set the mode of the Propixx projector. VPixx provides a Python toolbox to do this, but it didn't work the last time I checked.)
