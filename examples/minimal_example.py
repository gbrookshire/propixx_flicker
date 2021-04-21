"""
A minimal example of how to show flickering stimuli with the Propixx projector
in the 1440-Hz mode.
"""

from psychopy import visual, core, event

# Flickering stims on the Propixx projector
import propixx_flicker as fl

# Set use_propixx to False for testing on a normal monitor, or to True to run
# this on a Propixx projector
use_propixx = False

# Initialize the Propixx projector
fl.init(use_propixx=use_propixx)

flicker_freqs = [3, 63]  # Frequency of the flicker in Hz
stim_duration = 5  # in seconds
stim_size = 2 ** 7  # Size of the flickered stimulus in pixels


######################
# Window and Stimuli  #
######################

colors = {'grey': [0.0, 0.0, 0.0],
          'white': [1.0, 1.0, 1.0],
          'black': [-1.0, -1.0, -1.0],
          'cs': 'rgb'}

frame_center = (fl.FRAME_CENTER[0], fl.FRAME_CENTER[1])

win = visual.Window(fl.FULL_RES,
                    monitor='propixx_tester',
                    fullscr=True,
                    color=colors['grey'],
                    colorSpace=colors['cs'],
                    allowGUI=False, units='pix')

# Common parameters used across stimuli
stim_params = {'win': win, 'units': 'pix'}

# The QuadStim class arranges a stimulus across the different quadrants of the
# screen as it's broken up by the Propixx projector. You can give this class
# any psychopy.visual stimulus object, and it should be able to figure out all
# the arguments.
text_stim = fl.QuadStim(visual.TextStim,
                        text='hello',
                        pos=frame_center,
                        color=colors['white'],
                        colorSpace=colors['cs'],
                        height=30,
                        **stim_params)

# This module gives two ways to flicker the stimuli: by luminance (where
# everything flickers from maximal brightness to black) and by opacity (where
# everything flickers from white/black to neutral grey. They are used in the
# same way, but there are differences in the implementation. These classes
# automatically flicker the stimulus at the frequency specified, when in the
# greyscale 1440 Hz mode on the Propixx projector.
stim = fl.BrightnessFlickerStim(visual.ImageStim,
                                image='example_stimulus.jpg',
                                pos=frame_center,
                                mask='circle',
                                colorSpace=colors['cs'],
                                size=(stim_size, stim_size),
                                **stim_params)


####################
# Show the stimuli  #
####################

instructs = ['This example shows a flickering image.',
             'Ready?']
instructs = [f'{txt}\n\nPress SPACE to go on' for txt in instructs]


def show_text(text):
    """ Show text at the center of the screen.
    """
    text_stim.set('text', text)
    text_stim.draw()
    win.flip()


def instructions(text):
    """ Show instructions and go on after pressing space
    """
    show_text(text)
    event.waitKeys(keyList=['space'])
    win.flip(clearBuffer=True)  # clear the screen
    core.wait(0.2)


def main():
    """ Run the example experiment
    """

    # Show the instructions
    for txt in instructs:
        instructions(txt)

    # Show the flickering stimulus
    for freq in flicker_freqs:
        # Show a label of how fast the stimuli will flicker
        show_text(f"{freq} Hz")
        core.wait(1.0)
        # Show the flickering stimulus
        stim.flicker(freq)  # Set the flicker frequency
        onset_time = core.monotonicClock.getTime()
        while core.monotonicClock.getTime() < onset_time + stim_duration:
            stim.draw()  # Automatically updates the stimuli for freq-tagging
            win.flip()

        # Show a blank screen
        win.flip(clearBuffer=True)
        core.wait(0.5)

    win.close()
    core.quit()


if __name__ == '__main__':
    main()
