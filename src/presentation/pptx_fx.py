"""Slide transitions and entrance animations for python-pptx slides, written as OOXML.

Animation model: a slide has a list of steps. Each step starts on a click (or automatically
after the slide appears, for the first step only) and holds a list of beats. Shapes in one beat
start together; each beat starts when the previous beat ends plus its own delay.
"""
from lxml import etree

P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
MC = 'http://schemas.openxmlformats.org/markup-compatibility/2006'
P14 = 'http://schemas.microsoft.com/office/powerpoint/2010/main'
P159 = 'http://schemas.microsoft.com/office/powerpoint/2015/09/main'

# (presetID, presetSubtype, animEffect filter); 'rise' adds a short upward float to the fade
EFFECTS = {
    'fade': (10, 0, 'fade'),
    'rise': (42, 0, 'fade'),
    'wipe_left': (22, 8, 'wipe(left)'),
    'wipe_up': (22, 4, 'wipe(down)'),
}


class Beat:
    def __init__(self, shapes, effect='fade', dur=500, delay=0):
        self.shapes = list(shapes) if isinstance(shapes, (list, tuple)) else [shapes]
        self.effect, self.dur, self.delay = effect, dur, delay


class Timeline:
    def __init__(self):
        self.steps = []          # list of (trigger, [Beat])

    def auto(self, *beats):
        assert not self.steps, 'only the first step can start automatically'
        self.steps.append(('auto', list(beats)))
        return self

    def click(self, *beats):
        self.steps.append(('click', list(beats)))
        return self

    @property
    def n_clicks(self):
        return sum(1 for t, _ in self.steps if t == 'click')


def _behaviours(nid, spid, effect, dur):
    pid, sub, filt = EFFECTS[effect]
    tgt = f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'
    x = (f'<p:set><p:cBhvr><p:cTn id="{nid()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/>'
         f'</p:stCondLst></p:cTn>{tgt}<p:attrNameLst><p:attrName>style.visibility</p:attrName>'
         f'</p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>'
         f'<p:animEffect transition="in" filter="{filt}"><p:cBhvr><p:cTn id="{nid()}" dur="{dur}"/>'
         f'{tgt}</p:cBhvr></p:animEffect>')
    if effect == 'rise':
        for attr, start in (('ppt_x', '#ppt_x'), ('ppt_y', '#ppt_y+0.04')):
            end = '#' + attr
            x += (f'<p:anim calcmode="lin" valueType="num"><p:cBhvr><p:cTn id="{nid()}" dur="{dur}" '
                  f'decel="100000" fill="hold"/>{tgt}<p:attrNameLst><p:attrName>{attr}</p:attrName>'
                  f'</p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:strVal val="{start}"/>'
                  f'</p:val></p:tav><p:tav tm="100000"><p:val><p:strVal val="{end}"/></p:val></p:tav>'
                  f'</p:tavLst></p:anim>')
    return pid, sub, x


def timing_xml(tl):
    counter = [2]

    def nid():
        counter[0] += 1
        return counter[0]

    steps_xml = []
    for si, (trigger, beats) in enumerate(tl.steps):
        outer_id = nid()
        if trigger == 'auto':
            cond = '<p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond>'
        else:
            cond = '<p:cond delay="indefinite"/>'
        beat_xml, t = [], 0
        for bi, beat in enumerate(beats):
            t += beat.delay
            inner_id = nid()
            effs = []
            for k, shp in enumerate(beat.shapes):
                if bi == 0 and k == 0:
                    node = 'clickEffect' if trigger == 'click' else 'afterEffect'
                elif k == 0:
                    node = 'afterEffect'
                else:
                    node = 'withEffect'
                eid = nid()
                pid, sub, beh = _behaviours(nid, shp.shape_id, beat.effect, beat.dur)
                effs.append(f'<p:par><p:cTn id="{eid}" presetID="{pid}" presetClass="entr" '
                            f'presetSubtype="{sub}" fill="hold" grpId="0" nodeType="{node}">'
                            f'<p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>{beh}'
                            f'</p:childTnLst></p:cTn></p:par>')
            beat_xml.append(f'<p:par><p:cTn id="{inner_id}" fill="hold"><p:stCondLst>'
                            f'<p:cond delay="{t}"/></p:stCondLst><p:childTnLst>{"".join(effs)}'
                            f'</p:childTnLst></p:cTn></p:par>')
            t += beat.dur
        steps_xml.append(f'<p:par><p:cTn id="{outer_id}" fill="hold"><p:stCondLst>{cond}</p:stCondLst>'
                         f'<p:childTnLst>{"".join(beat_xml)}</p:childTnLst></p:cTn></p:par>')

    seen, bld = set(), []
    for _, beats in tl.steps:
        for beat in beats:
            for shp in beat.shapes:
                if shp.shape_id in seen:
                    raise ValueError(f'shape {shp.name} animated twice')
                seen.add(shp.shape_id)
                if shp.shape_type is not None and shp.element.tag.endswith('}sp'):
                    bld.append(f'<p:bldP spid="{shp.shape_id}" grpId="0" animBg="1"/>')
    return (f'<p:timing xmlns:p="{P}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" '
            f'nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" '
            f'dur="indefinite" nodeType="mainSeq"><p:childTnLst>{"".join(steps_xml)}</p:childTnLst>'
            f'</p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl>'
            f'</p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl>'
            f'<p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par>'
            f'</p:tnLst>' + (f'<p:bldLst>{"".join(bld)}</p:bldLst>' if bld else '') + '</p:timing>')


def transition_xml(kind, dur_ms):
    if kind == 'morph':
        return (f'<mc:AlternateContent xmlns:mc="{MC}"><mc:Choice xmlns:p159="{P159}" Requires="p159">'
                f'<p:transition xmlns:p="{P}" xmlns:p14="{P14}" spd="slow" p14:dur="{dur_ms}">'
                f'<p159:morph option="byObject"/></p:transition></mc:Choice><mc:Fallback>'
                f'<p:transition xmlns:p="{P}" spd="med"><p:fade/></p:transition></mc:Fallback>'
                f'</mc:AlternateContent>')
    if kind == 'fade':
        return (f'<mc:AlternateContent xmlns:mc="{MC}"><mc:Choice xmlns:p14="{P14}" Requires="p14">'
                f'<p:transition xmlns:p="{P}" spd="slow" p14:dur="{dur_ms}"><p:fade/></p:transition>'
                f'</mc:Choice><mc:Fallback><p:transition xmlns:p="{P}" spd="slow"><p:fade/></p:transition>'
                f'</mc:Fallback></mc:AlternateContent>')
    raise ValueError(kind)


def apply(slide, transition=None, dur_ms=800, timeline=None):
    """Attach a transition and/or a timeline to a slide, in schema order after clrMapOvr."""
    sld = slide.element
    for tag in ('transition', 'timing'):
        for el in sld.findall(f'{{{P}}}{tag}'):
            sld.remove(el)
    anchor = sld.find(f'{{{P}}}clrMapOvr')
    idx = list(sld).index(anchor) + 1
    if transition:
        sld.insert(idx, etree.fromstring(transition_xml(transition, dur_ms)))
        idx += 1
    if timeline and timeline.steps:
        sld.insert(idx, etree.fromstring(timing_xml(timeline)))
