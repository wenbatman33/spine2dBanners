#!/usr/bin/env python3
"""Build the original lucky-tiger Spine 3.8 advertising banner."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from ai_typography_material import material_fill


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/banners/champions-league-2026/series/07-lucky-tiger"
SOURCE = OUT / "source"
IMAGES = OUT / "spine-3.8/images"
RUNTIME = OUT / "spine-3.8/runtime"
QA = OUT / "qa"

WIDTH, HEIGHT = 620, 272
S = 2
DURATION = 0.97
TIGER_DISPLAY_HEIGHT = 400
BAG_DISPLAY_HEIGHT = 150
FONT_CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FONT_LATIN = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"


def cjk(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_CJK, size, index=2)


def crop_alpha(image: Image.Image, threshold: int = 3) -> Image.Image:
    image = image.convert("RGBA")
    bbox = image.getchannel("A").point(
        lambda value: 255 if value >= threshold else 0
    ).getbbox()
    if not bbox:
        raise RuntimeError("empty alpha layer")
    return image.crop(bbox)


def blue_key(image: Image.Image) -> Image.Image:
    """Extract the royal-blue studio screen with spill decontamination."""
    source = image.convert("RGB")
    result = Image.new("RGBA", source.size)
    output: list[tuple[int, int, int, int]] = []
    background = (1, 7, 247)
    for red, green, blue in source.getdata():
        dominance = blue - max(red, green)
        if dominance >= 178:
            alpha = 0
        elif dominance <= 36:
            alpha = 255
        else:
            alpha = round(255 * (178 - dominance) / (178 - 36))
        if alpha <= 3:
            output.append((0, 0, 0, 0))
            continue
        amount = alpha / 255
        # Undo the blue-screen contribution at antialiased edges.
        clean = []
        for value, back in zip((red, green, blue), background):
            corrected = (value - (1 - amount) * back) / max(0.02, amount)
            clean.append(max(0, min(255, round(corrected))))
        output.append((*clean, alpha))
    result.putdata(output)
    return crop_alpha(result, 4)


def resize_height(image: Image.Image, height: int) -> Image.Image:
    image = crop_alpha(image)
    width = round(image.width * height / image.height)
    return image.resize((width, height), Image.Resampling.LANCZOS)


def alpha_layer(mask: Image.Image, colour: tuple[int, int, int, int]) -> Image.Image:
    layer = Image.new("RGBA", mask.size, colour)
    layer.putalpha(ImageChops.multiply(mask, Image.new("L", mask.size, colour[3])))
    return layer


def gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGBA", size)
    draw = ImageDraw.Draw(image)
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        colour = tuple(round(a + (b - a) * t) for a, b in zip(top, bottom))
        draw.line((0, y, size[0], y), fill=(*colour, 255))
    return image


def dense_mask(text: str, font_size: int, max_width: int) -> Image.Image:
    scratch = Image.new("L", (480 * S, 90 * S), 0)
    font = cjk(font_size * S)
    draw = ImageDraw.Draw(scratch)
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text((12 * S - bbox[0], 8 * S - bbox[1]), text, font=font, fill=255)
    glyph = scratch.crop(scratch.getbbox()).filter(ImageFilter.MaxFilter(3))
    target = min(max_width * S, round(glyph.width * 0.92))
    return glyph.resize((target, glyph.height), Image.Resampling.LANCZOS)


def render_title() -> tuple[Image.Image, list[Image.Image]]:
    canvas = Image.new("RGBA", (350 * S, 126 * S), (0, 0, 0, 0))
    top_mask = Image.new("L", canvas.size, 0)
    bottom_mask = Image.new("L", canvas.size, 0)
    top = dense_mask("福运天天送", 46, 305)
    bottom = dense_mask("签到领豪礼", 42, 288)
    top_mask.paste(top, ((canvas.width - top.width) // 2, 4 * S))
    bottom_mask.paste(bottom, ((canvas.width - bottom.width) // 2, 64 * S))
    face = ImageChops.lighter(top_mask, bottom_mask)

    extrude = face.filter(ImageFilter.MaxFilter(19))
    for offset in range(7, 0, -1):
        shifted = Image.new("L", canvas.size, 0)
        shifted.paste(extrude, (offset * S, offset * S))
        canvas.alpha_composite(alpha_layer(shifted, (2, 24, 16 + offset * 4, 252)))
    canvas.alpha_composite(alpha_layer(face.filter(ImageFilter.MaxFilter(19)), (2, 20, 13, 255)))
    canvas.alpha_composite(alpha_layer(face.filter(ImageFilter.MaxFilter(11)), (39, 187, 86, 255)))
    canvas.alpha_composite(alpha_layer(face.filter(ImageFilter.MaxFilter(5)), (255, 205, 44, 255)))

    canvas.alpha_composite(material_fill(face, 2))
    upper = ImageChops.subtract(
        face,
        face.transform(face.size, Image.Transform.AFFINE, (1, 0, -2 * S, 0, 1, -2 * S), resample=Image.Resampling.BILINEAR),
    )
    canvas.alpha_composite(alpha_layer(upper, (255, 255, 216, 105)))

    bbox = canvas.getchannel("A").getbbox()
    title = canvas.crop(bbox)
    title_face = face.crop(bbox)
    glints: list[Image.Image] = []
    for index in range(6):
        centre = -20 * S + (title.width + 40 * S) * index / 5
        stripe = Image.new("L", title.size, 0)
        ImageDraw.Draw(stripe).polygon(
            [(centre - 7 * S, 0), (centre + 3 * S, 0), (centre + 40 * S, title.height), (centre + 28 * S, title.height)],
            fill=95,
        )
        stripe = stripe.filter(ImageFilter.GaussianBlur(2 * S))
        clipped = ImageChops.multiply(title_face, stripe).point(lambda value: round(value * 0.42))
        glint = Image.new("RGBA", title.size, (255, 255, 220, 0))
        glint.putalpha(clipped)
        glints.append(glint.resize((title.width // 2, title.height // 2), Image.Resampling.LANCZOS))
    return title, glints


def draw_centered(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font: ImageFont.FreeTypeFont, **kwargs: object) -> None:
    stroke = int(kwargs.get("stroke_width", 0))
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    left, top, right, bottom = box
    x = left + (right - left - (bbox[2] - bbox[0])) / 2 - bbox[0]
    y = top + (bottom - top - (bbox[3] - bbox[1])) / 2 - bbox[1]
    draw.text((round(x), round(y)), text, font=font, **kwargs)


def render_cta() -> Image.Image:
    image = Image.new("RGBA", (166 * S, 48 * S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    outer = [(13*S,2*S),(153*S,2*S),(164*S,24*S),(153*S,45*S),(13*S,45*S),(2*S,24*S)]
    shadow = [(x+2*S,y+2*S) for x,y in outer]
    draw.polygon(shadow, fill=(1, 24, 11, 245))
    draw.polygon(outer, fill=(243, 162, 16, 255))
    draw.line(outer+[outer[0]], fill=(255, 252, 161, 255), width=2*S)
    inner = [(16*S,7*S),(150*S,7*S),(157*S,24*S),(149*S,39*S),(17*S,39*S),(9*S,24*S)]
    draw.polygon(inner, fill=(23, 150, 74, 255))
    draw.line(inner+[inner[0]], fill=(95, 255, 158, 255), width=2*S)
    draw.line((22*S,10*S,144*S,10*S), fill=(255,255,214,245), width=2*S)
    draw_centered(draw,(12*S,7*S,154*S,40*S),"立即领取",cjk(22*S),fill=(255,255,219,255),stroke_width=2*S,stroke_fill=(2,52,22,255))
    return image


def render_bag_label() -> Image.Image:
    image = Image.new("RGBA", (158*S, 42*S), (0,0,0,0))
    draw = ImageDraw.Draw(image)
    draw_centered(draw,(2*S,0,156*S,42*S),"领 2,000 金币",cjk(24*S),fill=(255,237,91,255),stroke_width=3*S,stroke_fill=(1,72,25,255))
    return crop_alpha(image)


def render_kicker() -> Image.Image:
    image = Image.new("RGBA", (210*S, 28*S), (0,0,0,0))
    draw = ImageDraw.Draw(image)
    draw.text((2*S,-1*S),"LUCKY REWARDS",font=ImageFont.truetype(FONT_LATIN,22*S),fill=(136,255,182,255),stroke_width=S,stroke_fill=(0,64,35,255))
    return crop_alpha(image)


def prepare_images() -> dict[str, Image.Image]:
    background = Image.open(SOURCE / "background.png").convert("RGB").resize((WIDTH*S,HEIGHT*S),Image.Resampling.LANCZOS).convert("RGBA")
    tiger = resize_height(blue_key(Image.open(SOURCE / "tiger-blue.png")), 900)
    bag = resize_height(blue_key(Image.open(SOURCE / "bag-blue.png")), BAG_DISPLAY_HEIGHT * 3)
    title, glints = render_title()
    images = {"background":background,"tiger":tiger,"bag":bag,"title":title,"cta":render_cta(),"bag_label":render_bag_label(),"kicker":render_kicker()}
    for i, glint in enumerate(glints): images[f"title_glint_{i}"] = glint
    return images


def next_power(value: int) -> int:
    return 1 << math.ceil(math.log2(max(1, value)))


def pack(images: dict[str, Image.Image]) -> tuple[int,int]:
    padding, max_width = 6, 2048
    placements=[]; x=padding; y=padding; row_h=0
    for name,image in sorted(images.items(),key=lambda item:item[1].height,reverse=True):
        if x+image.width+padding>max_width:
            x=padding; y+=row_h+padding; row_h=0
        placements.append((name,x,y,image.width,image.height))
        x+=image.width+padding; row_h=max(row_h,image.height)
    used_w=max(x+w+padding for _,x,_,w,_ in placements)
    used_h=max(y+h+padding for _,_,y,_,h in placements)
    aw,ah=next_power(used_w),next_power(used_h)
    if aw>2048 or ah>2048: raise RuntimeError(f"atlas too large {aw}x{ah}")
    atlas=Image.new("RGBA",(aw,ah),(0,0,0,0))
    for name,x,y,_,_ in placements: atlas.alpha_composite(images[name],(x,y))
    path=RUNTIME/"banner.png"; atlas.save(path,optimize=True)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    lines=[f"banner.png?asset={digest}",f"size: {aw},{ah}","format: RGBA8888","filter: Linear,Linear","repeat: none"]
    for name,x,y,w,h in placements:
        lines += [name,"  rotate: false",f"  xy: {x}, {y}",f"  size: {w}, {h}",f"  orig: {w}, {h}","  offset: 0, 0","  index: -1"]
    (RUNTIME/"banner.atlas").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return aw,ah


def region(path: str, width: float, height: float) -> dict:
    return {"path":path,"width":round(width,3),"height":round(height,3)}


def mesh(image: Image.Image, columns: int=13, rows: int=13) -> dict:
    height=float(TIGER_DISPLAY_HEIGHT); width=image.width*height/image.height
    vertices=[]; uvs=[]; triangles=[]
    for row in range(rows):
        v=row/(rows-1)
        for col in range(columns):
            u=col/(columns-1)
            vertices += [round((u-.5)*width,4),round((1-v)*height,4)]
            uvs += [round(u,5),round(v,5)]
    for row in range(rows-1):
        for col in range(columns-1):
            a=row*columns+col; b=a+1; c=a+columns; d=c+1
            triangles += [a,c,b,b,c,d]
    return {"type":"mesh","path":"tiger","uvs":uvs,"triangles":triangles,"vertices":vertices,"hull":(columns*2+rows*2-4)*2,"width":round(width,3),"height":height}


def clamp(value: float) -> float:
    return max(0.0,min(1.0,value))


def rotate_delta(x: float,y: float,cx: float,cy: float,angle: float) -> tuple[float,float]:
    rad=math.radians(angle); dx=x-cx; dy=y-cy
    return (cx+dx*math.cos(rad)-dy*math.sin(rad)-x, cy+dx*math.sin(rad)+dy*math.cos(rad)-y)


def tiger_deform(image: Image.Image, arm_angle: float, head_angle: float, tail_y: float, body_squash: float, columns: int=13, rows: int=13) -> list[float]:
    height=float(TIGER_DISPLAY_HEIGHT); width=image.width*height/image.height
    offsets=[]
    for row in range(rows):
        v=row/(rows-1); y=(1-v)*height
        for col in range(columns):
            u=col/(columns-1); x=(u-.5)*width
            dx=0.0; dy=(.58-v)*body_squash*clamp((v-.3)/.45)
            left_w=clamp((.60-u)/.46)*clamp(1-abs(v-.31)/.24)
            ax,ay=rotate_delta(x,y,(.49-.5)*width,(1-.43)*height,arm_angle)
            dx+=ax*left_w; dy+=ay*left_w
            right_w=clamp((u-.52)/.35)*clamp(1-abs(v-.43)/.18)
            rx,ry=rotate_delta(x,y,(.55-.5)*width,(1-.45)*height,-arm_angle*.55)
            dx+=rx*right_w; dy+=ry*right_w
            head_w=clamp((.5-v)/.18)*clamp(1-abs(u-.56)/.42)
            hx,hy=rotate_delta(x,y,(.55-.5)*width,(1-.47)*height,head_angle)
            dx+=hx*head_w; dy+=hy*head_w
            tail_w=clamp((u-.68)/.3)*clamp(1-abs(v-.66)/.22)
            dy+=tail_y*tail_w*(.35+.65*clamp((u-.68)/.3))
            offsets += [round(dx,4),round(dy,4)]
    return offsets


def screen_bone(name: str,x: float,y: float,parent: str="root") -> dict:
    return {"name":name,"parent":parent,"x":round(x-WIDTH/2,3),"y":round(HEIGHT/2-y,3)}


def build_skeleton(images: dict[str,Image.Image]) -> dict:
    title_w=images["title"].width/S; title_h=images["title"].height/S
    bag_scale=images["bag"].height/BAG_DISPLAY_HEIGHT; bag_w=images["bag"].width/bag_scale
    bones=[{"name":"root"},{"name":"background","parent":"root"},screen_bone("title",230,78),{"name":"title_glint","parent":"title"},screen_bone("bag",88,210),{"name":"bag_label","parent":"bag","x":0,"y":-18},screen_bone("cta",250,222),screen_bone("tiger",490,420)]
    slots=[{"name":"background","bone":"background","attachment":"background"},{"name":"title","bone":"title","attachment":"title"},{"name":"title_glint","bone":"title_glint","attachment":"title_glint_0","blend":"additive","color":"ffffff38"},{"name":"bag","bone":"bag","attachment":"bag"},{"name":"bag_label","bone":"bag_label","attachment":"bag_label"},{"name":"cta","bone":"cta","attachment":"cta"},{"name":"tiger","bone":"tiger","attachment":"tiger"}]
    attachments={"background":{"background":region("background",WIDTH,HEIGHT)},"title":{"title":region("title",title_w,title_h)},"title_glint":{f"title_glint_{i}":region(f"title_glint_{i}",title_w,title_h) for i in range(6)},"bag":{"bag":region("bag",bag_w,BAG_DISPLAY_HEIGHT)},"bag_label":{"bag_label":region("bag_label",images["bag_label"].width/S,images["bag_label"].height/S)},"cta":{"cta":region("cta",images["cta"].width/S,images["cta"].height/S)},"tiger":{"tiger":mesh(images["tiger"])}}
    animation={"slots":{"title_glint":{"attachment":[{"time":round(.07+i*.13,3),"name":f"title_glint_{i}"} for i in range(6)]}},"bones":{"background":{"translate":[{"x":-3},{"time":.48,"x":3},{"time":DURATION,"x":-3}],"scale":[{"x":1.01,"y":1.01},{"time":.48,"x":1.025,"y":1.025},{"time":DURATION,"x":1.01,"y":1.01}]},"title":{"translate":[{}, {"time":.233,"x":-3,"y":5},{"time":.5},{"time":.733,"x":-3,"y":5},{"time":DURATION}]},"bag":{"translate":[{}, {"time":.5,"x":4,"y":3},{"time":DURATION}],"scale":[{}, {"time":.3,"x":.9,"y":1.06},{"time":.44,"x":1.08,"y":.92},{"time":DURATION}]},"bag_label":{"scale":[{}, {"time":.5,"x":1.09,"y":1.09},{"time":DURATION}]},"cta":{"scale":[{}, {"time":.233,"x":.95,"y":.95},{"time":.5},{"time":.733,"x":.95,"y":.95},{"time":DURATION}]},"tiger":{"translate":[{}, {"time":.333,"x":-3,"y":-9},{"time":.833,"x":-2,"y":6},{"time":DURATION}],"rotate":[{}, {"time":.5,"angle":-1.8},{"time":DURATION}]}},"deform":{"default":{"tiger":{"tiger":[{"vertices":tiger_deform(images["tiger"],-11,1.2,-3,0)},{"time":.2,"vertices":tiger_deform(images["tiger"],13,-1,4,2)},{"time":.5,"vertices":tiger_deform(images["tiger"],-15,-3,-5,-2)},{"time":.76,"vertices":tiger_deform(images["tiger"],12,1.5,5,1)},{"time":DURATION,"vertices":tiger_deform(images["tiger"],-11,1.2,-3,0)}]}}}}
    return {"skeleton":{"hash":"codex-lucky-tiger-v1","spine":"3.8.99","x":-310,"y":-136,"width":620,"height":272,"images":"./images/"},"bones":bones,"slots":slots,"skins":[{"name":"default","attachments":attachments}],"animations":{"animation":animation}}


def static_preview(images: dict[str,Image.Image]) -> None:
    preview=images["background"].copy()
    def paste_display(name: str,x: float,y: float,width: float|None=None,height: float|None=None,bottom: bool=False):
        layer=images[name]
        if height is not None:
            target_h=round(height*S); target_w=round(layer.width*target_h/layer.height)
        elif width is not None:
            target_w=round(width*S); target_h=round(layer.height*target_w/layer.width)
        else: target_w,target_h=layer.size
        if (target_w,target_h)!=layer.size: layer=layer.resize((target_w,target_h),Image.Resampling.LANCZOS)
        left=round(x*S-target_w/2); top=round(y*S-target_h if bottom else y*S-target_h/2)
        preview.alpha_composite(layer,(left,top))
    paste_display("title",230,78)
    paste_display("bag",88,210,height=BAG_DISPLAY_HEIGHT)
    paste_display("bag_label",88,228)
    paste_display("cta",250,222)
    paste_display("tiger",490,420,height=TIGER_DISPLAY_HEIGHT,bottom=True)
    preview.save(QA/"lucky-tiger-static.png",optimize=True)
    matte=Image.new("RGBA",(preview.width*2,preview.height),(24,25,29,255)); matte.alpha_composite(preview,(0,0))
    white=Image.new("RGBA",preview.size,(238,238,238,255)); tiger=images["tiger"].resize((round(images["tiger"].width*TIGER_DISPLAY_HEIGHT*S/images["tiger"].height),TIGER_DISPLAY_HEIGHT*S),Image.Resampling.LANCZOS); white.alpha_composite(tiger,(round(490*S-tiger.width/2),round(420*S-tiger.height))); matte.alpha_composite(white,(preview.width,0)); matte.save(QA/"lucky-tiger-matte.png",optimize=True)


def main() -> None:
    for directory in (IMAGES,RUNTIME,QA): directory.mkdir(parents=True,exist_ok=True)
    images=prepare_images()
    for name,image in images.items(): image.save(IMAGES/f"{name}.png",optimize=True)
    aw,ah=pack(images)
    skeleton=build_skeleton(images)
    (RUNTIME/"banner.json").write_text(json.dumps(skeleton,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    static_preview(images)
    print(json.dumps({"atlas":f"{aw}x{ah}","atlas_bytes":(RUNTIME/"banner.png").stat().st_size,"duration":DURATION,"mesh_vertices":13*13,"connected_character":True},indent=2))


if __name__ == "__main__": main()
