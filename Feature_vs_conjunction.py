"""
Feature vs. Conjunction Visual Search
PSY412 - Attention, Monsoon Semester 2026
Replication of Treisman & Gelade (1980), adapted from Johnson & Proctor
(2004, Figure 3.10).
"""

from psychopy import visual, core, event, data, gui, logging
import random
import os
import csv
import datetime

# ============================================================
# 0. CONFIGURATION -- the only section you should normally edit
# ============================================================

DEBUG = True            # True = few trials, for testing.
                         # Set to False before real data collection.

FULLSCREEN = True       # True = full-screen window

TRIALS_PER_CELL = 2 if DEBUG else 18   # trials per Search Type x Set Size x
                                        # Target Presence cell (proposal: 15-20)

SET_SIZES = [4, 8, 12, 16]
MAX_RT = 5.0             # seconds; trial times out and counts as a miss
FIXATION_DURATION = 0.5  # seconds
ITI_MIN, ITI_MAX = 0.5, 0.8   # seconds, jittered inter-trial interval
PRACTICE_TRIALS_PER_BLOCK = 8

RESPONSE_PRESENT_KEY = 'j'   # "target is present"
RESPONSE_ABSENT_KEY = 'f'    # "target is absent"

BAR_LENGTH = 40     # pixels, long axis of each bar
BAR_WIDTH = 8        # pixels, short axis of each bar
VERTICAL_ORI = 0
TILTED_ORI = 45       # "tilted 45 degrees to the left"

RED = (255, 0, 0)
GREEN = (0, 200, 0)

# ============================================================
# 1. PARTICIPANT INFO DIALOG
# ============================================================

exp_info = {
    'participant': '',
    'age': '',
    'block_order': ['feature_first', 'conjunction_first'],
}
dlg = gui.DlgFromDict(dictionary=exp_info, title='Feature vs Conjunction Search')
if not dlg.OK:
    core.quit()  # user pressed Cancel

exp_info['date'] = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

# make sure the data folder exists
os.makedirs('data', exist_ok=True)
data_filename = os.path.join(
    'data',
    f"P{exp_info['participant']}_{exp_info['date']}.csv"
)

# ============================================================
# 2. WINDOW AND STIMULI
# ============================================================

win = visual.Window(
    size=(1920, 1080),
    fullscr=FULLSCREEN,
    color=(170, 170, 170),
    colorSpace='rgb255',
    units='pix',
    allowGUI=not FULLSCREEN,
)
win.mouseVisible = not FULLSCREEN

fixation = visual.TextStim(win, text='+', height=40, color='black')

instructions_text = visual.TextStim(
    win, text='', height=28, color='black', wrapWidth=1100
)

feedback_text = visual.TextStim(win, text='', height=30, color='black')

# A 4x4 grid of possible bar locations, evenly spaced, covering the
# central part of the screen. We always have 16 candidate slots (to
# support the largest set size of 16) and randomly choose a subset
# for smaller set sizes. Small random jitter is added so the display
# does not look perfectly regular.
GRID_COLS, GRID_ROWS = 4, 4
GRID_SPACING_X, GRID_SPACING_Y = 150, 130
JITTER = 15  # pixels


def build_grid_positions():
    positions = []
    x_offset = -(GRID_COLS - 1) * GRID_SPACING_X / 2
    y_offset = -(GRID_ROWS - 1) * GRID_SPACING_Y / 2
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = x_offset + col * GRID_SPACING_X
            y = y_offset + row * GRID_SPACING_Y
            positions.append((x, y))
    return positions


ALL_GRID_POSITIONS = build_grid_positions()


def jittered(pos):
    x, y = pos
    return (x + random.uniform(-JITTER, JITTER),
            y + random.uniform(-JITTER, JITTER))


def make_bar(pos, color, ori):
    return visual.Rect(
        win, width=BAR_WIDTH, height=BAR_LENGTH,
        fillColor=color, lineColor=color,
        colorSpace='rgb255',
        pos=jittered(pos), ori=ori
    )


# ============================================================
# 3. TRIAL / DISPLAY CONSTRUCTION
# ============================================================

def build_display(search_type, feature_dim, set_size, target_present):
    """Return a list of visual.Rect bar stimuli for one trial."""
    positions = random.sample(ALL_GRID_POSITIONS, set_size)
    bars = []

    if search_type == 'feature':
        if feature_dim == 'color':
            # target: red vertical. distractors: green vertical.
            distractor_color, distractor_ori = GREEN, VERTICAL_ORI
            target_color, target_ori = RED, VERTICAL_ORI
        else:  # 'orientation'
            # target: red tilted. distractors: red vertical.
            distractor_color, distractor_ori = RED, VERTICAL_ORI
            target_color, target_ori = RED, TILTED_ORI

        n_distractors = set_size - 1 if target_present else set_size
        for i in range(n_distractors):
            bars.append(make_bar(positions[i], distractor_color, distractor_ori))
        if target_present:
            bars.append(make_bar(positions[-1], target_color, target_ori))

    else:  # 'conjunction'
        # target: red tilted.
        # distractor type A: red vertical (shares colour with target)
        # distractor type B: green tilted (shares orientation with target)
        n_distractors = set_size - 1 if target_present else set_size
        n_type_a = n_distractors // 2
        n_type_b = n_distractors - n_type_a

        idx = 0
        for i in range(n_type_a):
            bars.append(make_bar(positions[idx], RED, VERTICAL_ORI))
            idx += 1
        for i in range(n_type_b):
            bars.append(make_bar(positions[idx], GREEN, TILTED_ORI))
            idx += 1
        if target_present:
            bars.append(make_bar(positions[idx], RED, TILTED_ORI))

    return bars


# ============================================================
# 4. TRIAL LIST GENERATION
# ============================================================

def generate_trial_list(search_type):
    """Build a fully-crossed, randomised trial list for one block
    (one search type)."""
    trials = []
    feature_dims = ['color', 'orientation'] if search_type == 'feature' else [None]

    for set_size in SET_SIZES:
        for target_present in [True, False]:
            for feature_dim in feature_dims:
                n = TRIALS_PER_CELL if search_type == 'conjunction' else \
                    max(1, TRIALS_PER_CELL // len(feature_dims))
                for _ in range(n):
                    trials.append({
                        'search_type': search_type,
                        'feature_dim': feature_dim if feature_dim else 'NA',
                        'set_size': set_size,
                        'target_present': target_present,
                    })
    random.shuffle(trials)
    return trials


# ============================================================
# 5. CSV LOGGING
# ============================================================

csv_fields = [
    'participant', 'age', 'date', 'block_order',
    'block_index', 'trial_index_in_block',
    'search_type', 'feature_dim', 'set_size', 'target_present',
    'response', 'correct', 'rt', 'phase'
]

csv_file = open(data_filename, mode='w', newline='')
csv_writer = csv.DictWriter(csv_file, fieldnames=csv_fields)
csv_writer.writeheader()


def log_trial(block_index, trial_index, trial, response, correct, rt, phase='main'):
    csv_writer.writerow({
        'participant': exp_info['participant'],
        'age': exp_info['age'],
        'date': exp_info['date'],
        'block_order': exp_info['block_order'],
        'block_index': block_index,
        'trial_index_in_block': trial_index,
        'search_type': trial['search_type'],
        'feature_dim': trial['feature_dim'],
        'set_size': trial['set_size'],
        'target_present': trial['target_present'],
        'response': response,
        'correct': correct,
        'rt': rt,
        'phase': phase,
    })
    csv_file.flush()


# ============================================================
# 6. RUNNING A SINGLE TRIAL
# ============================================================

def run_trial(trial):
    # fixation
    fixation.draw()
    win.flip()
    core.wait(FIXATION_DURATION)

    # build and draw the search display
    bars = build_display(
        trial['search_type'], trial['feature_dim'],
        trial['set_size'], trial['target_present']
    )
    for bar in bars:
        bar.draw()
    win.flip()

    event.clearEvents()
    rt_clock = core.Clock()
    keys = event.waitKeys(
        maxWait=MAX_RT,
        keyList=[RESPONSE_PRESENT_KEY, RESPONSE_ABSENT_KEY, 'escape'],
        timeStamped=rt_clock
    )

    win.flip()  # clear display immediately after response

    if keys is None:
        response, rt = 'no_response', MAX_RT
    else:
        key, rt = keys[0]
        if key == 'escape':
            csv_file.close()
            win.close()
            core.quit()
        response = 'present' if key == RESPONSE_PRESENT_KEY else 'absent'

    correct_response = 'present' if trial['target_present'] else 'absent'
    correct = int(response == correct_response)

    # jittered inter-trial interval
    win.flip()
    core.wait(random.uniform(ITI_MIN, ITI_MAX))

    return response, correct, rt


# ============================================================
# 7. INSTRUCTIONS AND PRACTICE
# ============================================================

def show_text_screen(text, wait_for_key=True):
    instructions_text.text = text
    instructions_text.draw()
    win.flip()
    if wait_for_key:
        event.waitKeys(keyList=['space'])


def run_practice_block(search_type):
    practice_trials = generate_trial_list(search_type)[:PRACTICE_TRIALS_PER_BLOCK]
    n_correct = 0
    for i, trial in enumerate(practice_trials):
        response, correct, rt = run_trial(trial)
        n_correct += correct
        log_trial(block_index=-1, trial_index=i, trial=trial,
                   response=response, correct=correct, rt=rt, phase='practice')
        feedback_text.text = 'Correct!' if correct else 'Incorrect'
        feedback_text.color = 'green' if correct else 'red'
        feedback_text.draw()
        win.flip()
        core.wait(0.5)
    show_text_screen(
        f"Practice complete: {n_correct}/{len(practice_trials)} correct.\n\n"
        f"Press SPACE to begin the real trials."
    )


def run_main_block(search_type, block_index):
    trials = generate_trial_list(search_type)
    for i, trial in enumerate(trials):
        response, correct, rt = run_trial(trial)
        log_trial(block_index=block_index, trial_index=i, trial=trial,
                   response=response, correct=correct, rt=rt, phase='main')
        # self-paced rest break every 40 trials
        if (i + 1) % 40 == 0 and (i + 1) < len(trials):
            show_text_screen(
                f"Break. You have completed {i + 1} of {len(trials)} "
                f"trials in this block.\n\nPress SPACE to continue."
            )


# ============================================================
# 8. INSTRUCTION TEXTS
# ============================================================

GENERAL_INSTRUCTIONS = (
    "Welcome!\n\n"
    "In this experiment you will see a screen with several coloured bars. "
    "Your job is to decide whether a TARGET bar is present or absent.\n\n"
    f"Press '{RESPONSE_PRESENT_KEY.upper()}' if the target IS present.\n"
    f"Press '{RESPONSE_ABSENT_KEY.upper()}' if the target is NOT present.\n\n"
    "Respond as quickly and as accurately as you can.\n\n"
    "The experiment has two blocks. Before each block you will be told "
    "what the target looks like, and you will do a short practice.\n\n"
    "Press SPACE to continue."
)

FEATURE_INSTRUCTIONS = (
    "BLOCK: FEATURE SEARCH\n\n"
    "In this block, the target is a bar that looks DIFFERENT from all the "
    "other bars. It stands out because of its COLOUR or its TILT.\n\n"
    "For example:\n"
    "   - one red bar among green bars, or\n"
    "   - one tilted bar among upright bars.\n\n"
    f"If one bar stands out, press '{RESPONSE_PRESENT_KEY.upper()}' (target present).\n"
    f"If all the bars look the same, press '{RESPONSE_ABSENT_KEY.upper()}' (target absent).\n\n"
    "Press SPACE to start a short practice."
)

CONJUNCTION_INSTRUCTIONS = (
    "BLOCK: CONJUNCTION SEARCH\n\n"
    "In this block, the target is ONE bar that is RED and TILTED.\n\n"
    "The other bars are either red but upright, or green and tilted. "
    "Only the target is both red AND tilted.\n\n"
    f"If a red tilted bar is there, press '{RESPONSE_PRESENT_KEY.upper()}' (target present).\n"
    f"If there is no red tilted bar, press '{RESPONSE_ABSENT_KEY.upper()}' (target absent).\n\n"
    "Press SPACE to start a short practice."
)


# ============================================================
# 9. MAIN EXPERIMENT FLOW
# ============================================================

show_text_screen(GENERAL_INSTRUCTIONS)

if exp_info['block_order'] == 'feature_first':
    block_sequence = ['feature', 'conjunction']
else:
    block_sequence = ['conjunction', 'feature']

for block_num, search_type in enumerate(block_sequence):
    if search_type == 'feature':
        show_text_screen(FEATURE_INSTRUCTIONS)
    else:
        show_text_screen(CONJUNCTION_INSTRUCTIONS)
    run_practice_block(search_type)
    run_main_block(search_type, block_index=block_num)

show_text_screen(
    "You have finished the experiment.\n\nThank you for participating!\n\n"
    "Press SPACE to exit.",
)

csv_file.close()
win.close()
core.quit()