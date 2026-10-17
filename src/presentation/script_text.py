"""Speaker script, one English entry per slide.
Numbers are filled in from slide_numbers.compute(). [CLICK] marks one click; the deck builder
checks that each slide has exactly as many clicks as its animation timeline.
"""
import math


def script(N):
    r = round
    return [
        dict(
            en="Hi, I’m Jonas. Americans feel much worse about the economy than the numbers suggest. "
               "Is the news to blame? Our answer: mostly no."),
        dict(
            en=f"First, the gap. We predict the Michigan index from unemployment, inflation and GDP growth, "
               f"using only data known at the time. [CLICK] Blue is the prediction. [CLICK] Black is what "
               f"people say. [CLICK] The gap is about {r(-N['gap_2025'])} points in 2025 and "
               f"{r(-N['gap_2026'])} in 2026. The economy explains only about a tenth of the drop since 2019."),
        dict(
            en="Three explanations are possible: real pressures the headline numbers miss, like high prices; "
               "the media; or a problem with the survey or the model. [CLICK] We fixed all our tests in "
               "advance, including eight results that would count against the media story."),
        dict(
            en="Start with measurement. The gap is similar in every income, age, region and education group. "
               "[CLICK] The survey moved online in 2024, but the gap kept growing after that. [CLICK] "
               f"Party mix moves it by less than {int(N['party_bound']) + 1} points. [CLICK] And it was this "
               f"large before the campaign."),
        dict(
            en=f"Now the media. We collected about {r(N['corpus_items'], -3):,} news items, posts and comments. "
               f"An LLM coded over {int(N['coded_items']) // 1000 * 1000:,}, and two people labeled "
               f"{int(N['gold_items'])} by hand to check it. [CLICK] On tone, the LLM agrees with humans almost "
               f"as well as they agree with each other, and about twice as well as word lists. [CLICK] "
               f"Swapping political names showed no sign of bias."),
        dict(
            en=f"Coverage treats good and bad news alike, and only {int(N['fact_wrong'])} of "
               f"{int(N['fact_checkable'])} checkable numbers were wrong. [CLICK] What changed is blame: under "
               f"Trump’s second term, {r(100 * N['blame_trump2'])} percent of items blame the White House. "
               f"[CLICK] But tariffs are his own decisions, so blame is not proof of bias."),
        dict(
            en=f"The key test: does news tone help forecast sentiment? Each dot is one version of the test. "
               f"[CLICK] Added to the economy model, tone helps a little. [CLICK] But with household costs and "
               f"politics included, none of {int(N['m3_n_specs'])} versions is significant. [CLICK] At most, "
               f"tone explains about {math.ceil(100 * N['tone_share_max'])} percent of the gap."),
        dict(
            en="Back to our three explanations. [CLICK] Measurement is ruled out. [CLICK] The media story is "
               "weak: two of our eight tests go against it. [CLICK] Real pressures stay open: high prices may "
               "matter, but our data cannot size them. Next, an experiment could test cause."),
        dict(
            en=f"What does this mean for finance? [CLICK] In 2026 the index averages about {r(N['actual_2026'])}; "
               f"the economy points to {r(N['pred_2026'])}. [CLICK] That is below any reading before 2020, so "
               f"old models would see a deep downturn. [CLICK] So treat the gap as lasting, not noise. Track it "
               f"with its error band, next to prices and rates. News tone will not fix it. Thank you."),
    ]
