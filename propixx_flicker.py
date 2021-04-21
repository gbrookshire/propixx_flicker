""" Display flickering stimuli on a Propixx projector using Psychopy.

The Propixx projector allows you to display 12 low-resolution gray-scale frames
for each screen refresh. It does this by coding multiple frames in different
quadrants of the screen and in the three color channels.
Frames are selected like this:

for color_channel in (red, green, blue):
    for quadrant in range(4):
        show_data(quadrant, color_channel)

Quadrants of the screen are organized like so:
      1  2
      3  4
"""

__author__ = "Geoff Brookshire"
__license__ = "MIT"

import time
import copy
import numpy as np
from psychopy import visual
import pyglet.gl

FULL_RES = [1920, 1080] # Screen resolution provided by Propixx
FRAME_RES = [e/2 for e in FULL_RES] # Each frame fills 1/4 of the whole screen
FRAME_CENTER = [-FRAME_RES[0]/2, FRAME_RES[1]/2] # The center of the frame
_PROPIXX_ON = False # Set to True when the projector is ready for 1440 Hz


def init(use_propixx=True):
    """ Initialize the Propixx monitor to show stimuli at 1440
    """
    global OUTPUT_FRAME_RATE
    global _PROPIXX_ON
    if use_propixx:
        _set_propixx_mode(5) # 1440 Hz
        _PROPIXX_ON = True
        OUTPUT_FRAME_RATE = 120 # Sends multiplexed frames at 120 Hz
    else:
        OUTPUT_FRAME_RATE = 60 # Normal monitors refresh at 60 Hz
    print('Ready to display at {} Hz'.format(OUTPUT_FRAME_RATE))


def close():
    """ Revert projector to normal display mode
    """
    _set_propixx_mode(0) # Revert to normal version


class QuadStim(object):
    """ Class to show basic stimuli on a Propixx projector.
    This class takes a Psychopy stimulus object and duplicates it across the
    four quadrants of the screen.

    Arguments
    stim_class: A stimulus class from psychopy.visual
    pos: Position in the subframe (in pixel units)
    Other arguments to the stim initialization can be included
        after those arguments.
    """

    def __init__(self, stim_class, **kwargs):
        # Make a list of 4 Psychopy stimulus objects
        self.stimuli = [stim_class(**kwargs) for _ in range(4)]
        # Move them into the correct locations
        self.set_pos(kwargs['pos'])

    def set_pos(self, pos):
        """ Set the position of the stimulus in Propixx coordinates.
        """
        self.stimuli[0].pos = pos
        self.stimuli[1].pos = (pos[0] + FRAME_RES[0], pos[1])
        self.stimuli[2].pos = (pos[0], pos[1] - FRAME_RES[1])
        self.stimuli[3].pos = (pos[0] + FRAME_RES[0], pos[1] - FRAME_RES[1])

    def draw(self):
        """ Draw all four stimuli on the screen
        """
        for s in self.stimuli:
            s.draw()

    def set(self, attr, value):
        """ Set a stimulus attribute across all quadrants of the screen.
        """
        if attr == 'pos':
            self.set_pos(value)
        else:
            for s in self.stimuli:
                setattr(s, attr, value)


class OpacityFlickerStim(QuadStim):
    """ Class to flicker the opacity of stimuli with a Propixx projector.

    Arguments: Same as for QuadStim 

    Set the frequency of the flicker with the `.flicker()` method. For the
    flickering to work correctly, the stimulus needs to be re-drawn with the
    `.draw()` method on every screen refresh.
    """

    def __init__(self, stim_class, **kwargs):
        super(OpacityFlickerStim, self).__init__(stim_class, **kwargs)
        self.flickering = False
        self.phase = 0.0

    def draw(self):
        self._multiplex()
        super(OpacityFlickerStim, self).draw()

    def _next(self):
        """
        Get the opacity for the next Propixx-level 1440-Hz frame of the stim.
        This method implements sinusoidal flickering, but could be overwritten
        to use different kinds of flickering.

        For example, either of these snippets could be swapped in:
        (Make sure opacity varies between 0 and 1, or you'll get weird results)

        # Square-wave modulation
        if self.phase <= np.pi:
            opacity = 1.0
        else:
            opacity = 0.0

        # Sawtooth modulation
        opacity = self.phase / (2 * np.pi)

        """
        self.phase += self._freq
        self.phase = np.mod(self.phase, 2 * np.pi) # wrap to 2pi

        # Sinusoidal modulation
        opacity = 0.5 * (1 + np.cos(self.phase)) # Between 0 and 1

        return opacity

    def _multiplex(self):
        """
        Get the state for the next 12 Propixx frames, and combine them into
        one frame to be sent from the stimulus presentation computer to the
        Propixx projector. This function adjusts the stimulus characteristics
        so that the stimulus can be presented with the draw() method.
        """

        # Don't change anything if the stimulus isn't changing
        if not self.flickering:
            return None

        # Opacity of each Propixx frame
        opacity = [self._next() for _ in range(12)]

        # Combine into RGB color images in each quadrant of the screen
        # Index columns to get adjustment for one quadrant
        opacity = np.reshape(opacity, [3,4], order='C')

        self._assign_mux_colors(opacity)

    def _assign_mux_colors(self, colors):
        # Change the color for the images in each quadrant
        for n_quad in range(4):
            c = colors[:,n_quad] # Color channel adjustments for this column
            self.stimuli[n_quad].color = c

    def flicker(self, freq=0.0):
        """ Flicker the stimuli by adjusting the opacity.
        """
        self.phase = 0 # Reset the phase to zero
        self.flicker_freq = freq # Frequency in Hz
        # Find amount of phase change between each Propixx frame
        self._freq = self.flicker_freq * 2 * np.pi / OUTPUT_FRAME_RATE / 12
        if self.flicker_freq != 0:
            self.flickering = True
        else:
            self.flickering = False


class BrightnessFlickerStim(OpacityFlickerStim):
    """ Class to flicker the brightness of stimuli with a Propixx projector.

    Arguments: Same as for QuadStim 

    Set the frequency of the flicker with the `.flicker()` method. For the
    flickering to work correctly, the stimulus needs to be re-drawn with the
    `.draw()` method on every screen refresh.
    """

    def __init__(self, stim_class, **kwargs):
        # Set up the color filters
        filter_params = copy.copy(kwargs)
        filter_params['image'] = np.ones(kwargs['size'])
        self.image_filters = QuadStim(visual.ImageStim, **filter_params)
        # Overlay a masking stimulus with a circular hole in the middle
        if 'mask' in kwargs:
            if kwargs['mask'] == 'circle':
                self.masked = True
                mask_params = copy.copy(kwargs)
                mask_params['image'] = np.ones(kwargs['size'])
                mask_params['color'] = kwargs['win'].color
                mask_params['mask'] = _inv_circle_mask(kwargs['size'][0])
                self.mask_stimuli = QuadStim(visual.ImageStim, **mask_params)
            else:
                m = 'BrightnessFlickerStim has only been ' \
                    'implemented with circular masks'
                raise NotImplementedError(m)
        else:
            self.masked = False
        super(BrightnessFlickerStim, self).__init__(stim_class, **kwargs)

    def set_pos(self, pos):
        super(BrightnessFlickerStim, self).set_pos(pos)
        self.image_filters.set_pos(pos)
        if self.masked:
            self.mask_stimuli.set_pos(pos)

    def _assign_mux_colors(self, colors):
        """ Instead of changing the stimuli, change the colors of
            color filters in front of the stimuli.
        """
        # Rescale from 0-1 to (-1)-1
        colors = (colors * 2) - 1
        # Change the color for the images in each quadrant
        for n_quad in range(4):
            c = colors[:,n_quad]
            self.image_filters.stimuli[n_quad].color = c

    def draw(self):
        ''' To fade the picture to black instead of inverting the colors,
            we have to temporarily change the OpenGL blend function.
            This was suggested by Damien Mannion on the Psychopy list.
        '''
        # Set up the color filters
        self._multiplex()
        # Draw the face stimuli
        for s in self.stimuli:
            s.draw()
        # # Change the OpenGL blend mode
        pyglet.gl.glBlendFunc(pyglet.gl.GL_DST_COLOR,
                              pyglet.gl.GL_ZERO)
        # Draw the filters
        self.image_filters.draw()
        # reset the blend mode
        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA,
                              pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
        # Draw the mask stimuli
        if self.masked:
            self.mask_stimuli.draw()


def _inv_circle_mask(size):
    """ Return a circular boolean mask
    size: int
    """
    radius = size / 2
    radslice = slice(-int(radius), int(radius))
    x,y = np.ogrid[radslice, radslice]
    r2 = x**2 + y**2 # Matrix of the distance from center of matrix
    circmask = r2 <= radius**2 # circular mask
    circmask = ~circmask # Invert the mask
    circmask = circmask * 2 - 1 # Rescale to (-1)-1
    return circmask


def _set_propixx_mode(vpixx_mode):
    """
    Set the mode of the VPixx projector
    """
    mlab_cmd = "Datapixx('Open'); \
                Datapixx('SetPropixxDlpSequenceProgram', {}); \
                Datapixx('RegWrRd'); \
                exit;"
    _call_matlab(mlab_cmd.format(vpixx_mode))


def _call_matlab(matlab_cmd):
    """ Invoke Matlab through the windows Command Prompt

    No error handling, so this could break without telling you why if Matlab
    changes. (Sorry, future users)

    """
    shell_cmd = 'matlab -nodisplay -nosplash -nodesktop -r "{}" '
    cmd = shell_cmd.format(matlab_cmd)
    status = subprocess.check_output(cmd, shell=True)
    time.sleep(5) # Wait for everything to update
