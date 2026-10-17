"""Speaker script, English (to be read) and Chinese (for reference), one entry per slide.
Numbers are filled in from slide_numbers.compute(). [CLICK] marks one click; the deck builder
checks that each slide has exactly as many clicks as its animation timeline.
"""
import math


def script(N):
    r = round
    return [
        dict(
            en="Hi, I’m Jonas. Americans feel much worse about the economy than the numbers suggest. "
               "Is the news to blame? Our answer: mostly no.",
            zh="大家好，我是 Jonas。美国人对经济的感受比数据显示的差得多。这要怪新闻吗？我们的答案是：基本不是。"),
        dict(
            en=f"First, the gap. We predict the Michigan index from unemployment, inflation and GDP growth, "
               f"using only data known at the time. [CLICK] Blue is the prediction. [CLICK] Black is what "
               f"people say. [CLICK] The gap is about {r(-N['gap_2025'])} points in 2025 and "
               f"{r(-N['gap_2026'])} in 2026. The economy explains only about a tenth of the drop since 2019.",
            zh=f"先看缺口。我们用失业率、通胀和 GDP 增长来预测密歇根消费者信心指数，而且只用当时已知的数据。"
               f"[点击] 蓝线是预测值。[点击] 黑线是人们实际的回答。[点击] 缺口在 2025 年约 {r(-N['gap_2025'])} 点，"
               f"2026 年约 {r(-N['gap_2026'])} 点。2019 年以来的下降，经济数据只能解释大约十分之一。"),
        dict(
            en="Three explanations are possible: real pressures the headline numbers miss, like high prices; "
               "the media; or a problem with the survey or the model. [CLICK] We fixed all our tests in "
               "advance, including eight results that would count against the media story.",
            zh="可能的解释有三种：一是头条数据没有反映的真实压力，比如物价太高；二是媒体；三是调查或模型本身的问题。"
               "[点击] 所有检验都是事先定好的，其中包括八条一旦出现就不利于媒体解释的结果。"),
        dict(
            en="Start with measurement. The gap is similar in every income, age, region and education group. "
               "[CLICK] The survey moved online in 2024, but the gap kept growing after that. [CLICK] "
               f"Party mix moves it by less than {int(N['party_bound']) + 1} points. [CLICK] And it was this "
               f"large before the campaign.",
            zh="先看测量问题。各个收入、年龄、地区和学历组的缺口都差不多。[点击] 2024 年调查改成了线上，但之后缺口还在扩大。"
               f"[点击] 党派构成的变化最多只带来不到 {int(N['party_bound']) + 1} 点。[点击] 而且竞选开始之前缺口就已经这么大了。"),
        dict(
            en=f"Now the media. We collected about {r(N['corpus_items'], -3):,} news items, posts and comments. "
               f"An LLM coded over {int(N['coded_items']) // 1000 * 1000:,}, and two people labeled "
               f"{int(N['gold_items'])} by hand to check it. [CLICK] On tone, the LLM agrees with humans almost "
               f"as well as they agree with each other, and about twice as well as word lists. [CLICK] "
               f"Swapping political names showed no sign of bias.",
            zh=f"再看媒体。我们收集了约 {N['corpus_items'] / 1e4:.1f} 万条新闻、帖子和评论，用大语言模型编码了其中一万一千多条，"
               f"并请两个人独立手工标注了 {int(N['gold_items'])} 条来检验。[点击] 在语气上，模型和人的一致程度几乎和两个人之间一样高，"
               f"大约是词典法的两倍。[点击] 把政治人物的名字互换之后，也没有发现偏差。"),
        dict(
            en=f"Coverage treats good and bad news alike, and only {int(N['fact_wrong'])} of "
               f"{int(N['fact_checkable'])} checkable numbers were wrong. [CLICK] What changed is blame: under "
               f"Trump’s second term, {r(100 * N['blame_trump2'])} percent of items blame the White House. "
               f"[CLICK] But tariffs are his own decisions, so blame is not proof of bias.",
            zh=f"报道对好消息和坏消息的处理差不多，能核对的 {int(N['fact_checkable'])} 个数字里只有 {int(N['fact_wrong'])} 个是错的。"
               f"[点击] 变化最大的是归咎：特朗普第二任期内，{r(100 * N['blame_trump2'])}% 的报道把问题归咎于白宫。"
               f"[点击] 但关税本来就是总统自己的决定，所以归咎不能证明有偏差。"),
        dict(
            en=f"The key test: does news tone help forecast sentiment? Each dot is one version of the test. "
               f"[CLICK] Added to the economy model, tone helps a little. [CLICK] But with household costs and "
               f"politics included, none of {int(N['m3_n_specs'])} versions is significant. [CLICK] At most, "
               f"tone explains about {math.ceil(100 * N['tone_share_max'])} percent of the gap.",
            zh=f"关键检验：新闻语气能不能帮助预测消费者信心？每个点是检验的一个版本。[点击] 只加在经济模型上时，语气有一点帮助。"
               f"[点击] 但加入家庭成本和政治因素之后，{int(N['m3_n_specs'])} 个版本没有一个显著。[点击] "
               f"语气最多只能解释缺口的约 {math.ceil(100 * N['tone_share_max'])}%。"),
        dict(
            en="Back to our three explanations. [CLICK] Measurement is ruled out. [CLICK] The media story is "
               "weak: two of our eight tests go against it. [CLICK] Real pressures stay open: high prices may "
               "matter, but our data cannot size them. Next, an experiment could test cause.",
            zh="回到三种解释。[点击] 测量问题被排除了。[点击] 媒体解释很弱：八条预设检验中有两条与它相反。[点击] "
               "真实压力还没有定论：高物价可能有影响，但我们的数据无法量化。下一步可以用实验来检验因果。"),
        dict(
            en=f"What does this mean for finance? [CLICK] In 2026 the index averages about {r(N['actual_2026'])}; "
               f"the economy points to {r(N['pred_2026'])}. [CLICK] That is below any reading before 2020, so "
               f"old models would see a deep downturn. [CLICK] So treat the gap as lasting, not noise. Track it "
               f"with its error band, next to prices and rates. News tone will not fix it. Thank you.",
            zh=f"这对金融意味着什么？[点击] 2026 年这个指数平均约 {r(N['actual_2026'])}，经济数据指向 {r(N['pred_2026'])}。"
               f"[点击] 这比 2020 年以前的任何读数都低，按旧规律建的模型会把它看成深度衰退。[点击] "
               f"所以要把缺口当成持续的状态，而不是噪音；连同误差带一起跟踪它，同时看物价和利率。新闻语气修正不了它。谢谢大家。"),
    ]
