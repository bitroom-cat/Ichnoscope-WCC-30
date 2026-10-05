import os
import math
import random
import subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_motion_graphic():
    width = 1280
    height = 720
    fps = 30
    duration_sec = 5.6
    total_frames = int(fps * duration_sec)
    
    font_title_path = "C:/Windows/Fonts/bahnschrift.ttf"
    font_sub_path = "C:/Windows/Fonts/segoeui.ttf"
    font_mono_path = "C:/Windows/Fonts/consola.ttf"
    
    font_manual = ImageFont.truetype(font_title_path, 82)
    font_manual_sub = ImageFont.truetype(font_mono_path, 24)
    
    font_ichno = ImageFont.truetype(font_title_path, 94)
    font_ichno_sub = ImageFont.truetype(font_sub_path, 34)
    font_badge = ImageFont.truetype(font_mono_path, 18)
    
    # Pre-render "Manual Triage" text mask to create polygon shards
    manual_txt = "MANUAL TRIAGE"
    bbox = font_manual.getbbox(manual_txt)
    txt_w = bbox[2] - bbox[0]
    txt_h = bbox[3] - bbox[1]
    
    text_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(text_img)
    x_pos = (width - txt_w) // 2
    y_pos = (height - txt_h) // 2 - 30
    d.text((x_pos, y_pos), manual_txt, font=font_manual, fill=(220, 90, 90, 255))
    
    # Generate shards based on grid cells and Voronoi/triangles
    random.seed(42)
    shards = []
    cell_size = 28
    
    for cy in range(y_pos - 10, y_pos + txt_h + 20, cell_size):
        for cx in range(x_pos - 20, x_pos + txt_w + 30, cell_size):
            # Sample point inside bounding box
            center_x = cx + random.uniform(2, cell_size - 2)
            center_y = cy + random.uniform(2, cell_size - 2)
            
            # Check if this cell overlaps text pixels
            sample_box = (max(0, int(cx)), max(0, int(cy)), min(width, int(cx + cell_size)), min(height, int(cy + cell_size)))
            crop = text_img.crop(sample_box)
            alpha_arr = np.array(crop)[:, :, 3] if crop.size[0] > 0 and crop.size[1] > 0 else np.array([])
            
            if np.any(alpha_arr > 30):
                # Form polygon vertices around center
                num_pts = random.randint(3, 5)
                pts = []
                base_angle = random.uniform(0, 2 * math.pi)
                for i in range(num_pts):
                    ang = base_angle + (i / num_pts) * 2 * math.pi + random.uniform(-0.3, 0.3)
                    r = random.uniform(8, 20)
                    pts.append([r * math.cos(ang), r * math.sin(ang)])
                
                # Explosion velocity away from center
                dx = center_x - width / 2
                dy = center_y - (y_pos + txt_h / 2)
                dist = max(10, math.sqrt(dx * dx + dy * dy))
                speed = random.uniform(14, 38) * (1.0 + (dist / 150))
                angle = math.atan2(dy, dx) + random.uniform(-0.35, 0.35)
                
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed - random.uniform(3, 10) # initial upward kick
                
                rot_speed = random.uniform(-0.25, 0.25)
                
                shards.append({
                    "orig_cx": center_x,
                    "orig_cy": center_y,
                    "pts": np.array(pts, dtype=np.float32),
                    "vx": vx,
                    "vy": vy,
                    "rot_speed": rot_speed,
                    "color": (random.randint(180, 240), random.randint(60, 100), random.randint(70, 110)),
                    "size_scale": random.uniform(0.8, 1.3)
                })

    # Floating background cyber particles
    bg_particles = []
    for _ in range(70):
        bg_particles.append({
            "x": random.uniform(0, width),
            "y": random.uniform(0, height),
            "vx": random.uniform(-0.4, 0.4),
            "vy": random.uniform(-0.3, 0.3),
            "radius": random.uniform(1.0, 2.5),
            "alpha": random.uniform(0.15, 0.5),
            "color": random.choice([(140, 90, 255), (60, 210, 255), (100, 150, 255)])
        })

    # Prepare temp frames dir
    temp_dir = "d:/Ichnoscope-WCC-30/temp/motion_frames"
    os.makedirs(temp_dir, exist_ok=True)
    
    shatter_frame = 38
    print(f"Total shards generated: {len(shards)}")
    print(f"Rendering {total_frames} frames...")

    for frame_idx in range(total_frames):
        t = frame_idx / fps
        img = Image.new("RGB", (width, height), (11, 13, 19))
        draw = ImageDraw.Draw(img)
        
        # 1. Background grid & cyber particles
        # Subtle horizontal & vertical perspective lines
        grid_alpha = 18
        for gx in range(0, width, 64):
            draw.line([(gx, 0), (gx, height)], fill=(30, 38, 55, grid_alpha))
        for gy in range(0, height, 64):
            draw.line([(gx, gy), (width, gy)], fill=(30, 38, 55, grid_alpha))
            
        # Draw floating particles
        for p in bg_particles:
            px = (p["x"] + p["vx"] * frame_idx) % width
            py = (p["y"] + p["vy"] * frame_idx) % height
            pa = int(p["alpha"] * 255 * (0.8 + 0.2 * math.sin(frame_idx * 0.1 + px)))
            r = p["radius"]
            draw.ellipse([(px - r, py - r), (px + r, py + r)], fill=(p["color"][0], p["color"][1], p["color"][2]))

        # Convert to numpy for fast graphics operations
        frame_cv = np.array(img)
        frame_cv = cv2.cvtColor(frame_cv, cv2.COLOR_RGB2BGR)

        # -------------------------------------------------------------
        # PHASE 1: "MANUAL TRIAGE" (Frames 0 to shatter_frame)
        # -------------------------------------------------------------
        if frame_idx < shatter_frame:
            # Fade in during first 10 frames
            alpha = min(1.0, frame_idx / 12.0)
            
            # Subtle red breathing pulse
            pulse = 0.85 + 0.15 * math.sin(frame_idx * 0.25)
            red_intensity = int(220 * pulse)
            
            # Jitter slightly as shatter nears (frame 28 to 38)
            jx = 0
            jy = 0
            if frame_idx > 26:
                shake = (frame_idx - 26) * 0.6
                jx = random.uniform(-shake, shake)
                jy = random.uniform(-shake, shake)
            
            # Draw on PIL overlay
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            odraw = ImageDraw.Draw(overlay)
            
            # Red glow layer
            glow_col = (red_intensity, 40, 50, int(70 * alpha))
            odraw.text((x_pos + jx - 2, y_pos + jy), manual_txt, font=font_manual, fill=glow_col)
            odraw.text((x_pos + jx + 2, y_pos + jy), manual_txt, font=font_manual, fill=glow_col)
            odraw.text((x_pos + jx, y_pos + jy - 2), manual_txt, font=font_manual, fill=glow_col)
            odraw.text((x_pos + jx, y_pos + jy + 2), manual_txt, font=font_manual, fill=glow_col)
            
            # Sharp main text
            main_col = (int(235 * alpha), int(95 * alpha), int(95 * alpha), int(255 * alpha))
            odraw.text((x_pos + jx, y_pos + jy), manual_txt, font=font_manual, fill=main_col)
            
            # Subtitle
            sub_txt = "[ SLOW • FRAGMENTED • INCIDENT FATIGUE ]"
            sbbox = font_manual_sub.getbbox(sub_txt)
            sx = (width - (sbbox[2] - sbbox[0])) // 2
            sy = y_pos + txt_h + 30
            odraw.text((sx + jx, sy + jy), sub_txt, font=font_manual_sub, fill=(160, 80, 80, int(200 * alpha)))
            
            # Crack lines forming on frames 25-38
            if frame_idx >= 25:
                crack_progress = (frame_idx - 25) / 13.0
                cracks = [
                    [(x_pos + 120, y_pos + 20), (x_pos + 180, y_pos + 50), (x_pos + 230, y_pos + 45), (x_pos + 290, y_pos + 80)],
                    [(x_pos + 380, y_pos + 10), (x_pos + 410, y_pos + 40), (x_pos + 450, y_pos + 30), (x_pos + 490, y_pos + 70)],
                    [(x_pos + 280, y_pos + 50), (x_pos + 330, y_pos + 75)],
                ]
                for crack in cracks:
                    max_pt = int(len(crack) * crack_progress) + 1
                    for ci in range(min(max_pt, len(crack) - 1)):
                        pt1 = crack[ci]
                        pt2 = crack[ci+1]
                        odraw.line([pt1, pt2], fill=(255, 140, 50, 240), width=2)
            
            # Merge overlay
            img_rgba = Image.fromarray(cv2.cvtColor(frame_cv, cv2.COLOR_BGR2RGBA))
            img_rgba = Image.alpha_composite(img_rgba, overlay)
            frame_cv = cv2.cvtColor(np.array(img_rgba), cv2.COLOR_RGBA2BGR)

        # -------------------------------------------------------------
        # PHASE 2: SHATTER & EXPLOSION (shatter_frame to shatter_frame + 45)
        # -------------------------------------------------------------
        if frame_idx >= shatter_frame and frame_idx < (shatter_frame + 45):
            df = frame_idx - shatter_frame
            dt = df / fps
            
            # Shockwave ring
            shock_r = int(dt * 700)
            shock_alpha = max(0, 1.0 - (df / 35.0))
            if shock_alpha > 0 and shock_r > 0:
                cv2.circle(frame_cv, (width // 2, y_pos + txt_h // 2), shock_r, (int(255 * shock_alpha), int(200 * shock_alpha), int(255 * shock_alpha)), max(1, int(4 * shock_alpha)))
                cv2.circle(frame_cv, (width // 2, y_pos + txt_h // 2), int(shock_r * 0.85), (int(80 * shock_alpha), int(60 * shock_alpha), int(255 * shock_alpha)), max(1, int(2 * shock_alpha)))
            
            # Flash at moment of shatter (frames 38-42)
            if df < 5:
                flash_val = int((1.0 - df / 5.0) * 110)
                frame_cv = cv2.add(frame_cv, np.full_like(frame_cv, flash_val))
            
            # Draw moving shards
            gravity = 650.0
            shard_fade = max(0.0, 1.0 - (df / 40.0))
            
            for s in shards:
                cur_x = s["orig_cx"] + s["vx"] * dt
                cur_y = s["orig_cy"] + s["vy"] * dt + 0.5 * gravity * (dt ** 2)
                cur_rot = s["rot_speed"] * df
                
                # Rotate points
                cos_r = math.cos(cur_rot)
                sin_r = math.sin(cur_rot)
                R = np.array([[cos_r, -sin_r], [sin_r, cos_r]], dtype=np.float32)
                transformed_pts = (s["pts"] @ R.T) * s["size_scale"] + np.array([cur_x, cur_y])
                int_pts = np.int32([transformed_pts])
                
                col = (int(s["color"][2] * shard_fade), int(s["color"][1] * shard_fade), int(s["color"][0] * shard_fade))
                cv2.fillPoly(frame_cv, int_pts, col)
                # shard glowing border
                cv2.polylines(frame_cv, int_pts, True, (int(255 * shard_fade), int(150 * shard_fade), int(100 * shard_fade)), 1)

        # -------------------------------------------------------------
        # PHASE 3: ICHNOSCOPE EMERGENCE & REVELATION
        # -------------------------------------------------------------
        ichno_start = 58
        if frame_idx >= ichno_start:
            it = (frame_idx - ichno_start) / fps
            fade_in = min(1.0, it / 0.8) # 0 to 1 over 0.8s
            
            # Lens flare / radial bloom in center
            if it < 1.2:
                burst_radius = int(min(width, (it / 1.2) * 550))
                burst_alpha = max(0.0, math.sin(it / 1.2 * math.pi) * 0.4)
                overlay_b = frame_cv.copy()
                cv2.circle(overlay_b, (width // 2, height // 2 - 25), burst_radius, (255, 120, 200), -1)
                cv2.addWeighted(overlay_b, burst_alpha, frame_cv, 1.0 - burst_alpha, 0, frame_cv)

            # Pillow layer for smooth typography & neon glow
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            odraw = ImageDraw.Draw(overlay)
            
            ichno_txt = "ICHNOSCOPE"
            ibbox = font_ichno.getbbox(ichno_txt)
            iw = ibbox[2] - ibbox[0]
            ih = ibbox[3] - ibbox[1]
            
            ix = (width - iw) // 2
            iy = (height - ih) // 2 - 45
            
            # Glowing drop shadow layers (cyan & purple)
            glow_layers = [
                (12, (168, 85, 247, int(50 * fade_in))),   # purple outer
                (8, (56, 189, 248, int(80 * fade_in))),    # cyan mid
                (4, (192, 132, 252, int(120 * fade_in))),  # lilac inner
            ]
            for radius, col in glow_layers:
                for off_x in (-radius, 0, radius):
                    for off_y in (-radius, 0, radius):
                        if off_x != 0 or off_y != 0:
                            odraw.text((ix + off_x, iy + off_y), ichno_txt, font=font_ichno, fill=col)
            
            # Sharp bright text: Pure white with electric cyan tint
            odraw.text((ix, iy), ichno_txt, font=font_ichno, fill=(245, 252, 255, int(255 * fade_in)))
            
            # Dynamic horizontal accent divider bar
            bar_start = ichno_start + 15
            if frame_idx >= bar_start:
                bar_t = min(1.0, (frame_idx - bar_start) / 25.0)
                bar_max_w = iw + 120
                bar_w = bar_max_w * (1.0 - math.pow(1.0 - bar_t, 3)) # cubic ease out
                bx1 = (width - bar_w) / 2
                bx2 = bx1 + bar_w
                by = iy + ih + 22
                
                # Glowing gradient line
                odraw.line([(bx1, by), (bx2, by)], fill=(56, 189, 248, int(240 * bar_t)), width=3)
                odraw.line([(bx1, by-1), (bx2, by-1)], fill=(168, 85, 247, int(150 * bar_t)), width=1)
                odraw.line([(bx1, by+1), (bx2, by+1)], fill=(168, 85, 247, int(150 * bar_t)), width=1)
                
                # Diamond reticle in center
                cx = width / 2
                d_size = 5
                odraw.polygon([(cx, by - d_size), (cx + d_size, by), (cx, by + d_size), (cx - d_size, by)], fill=(255, 255, 255, int(255 * bar_t)))

            # Subtitle: "Event-Driven Agent Orchestration"
            sub_start = ichno_start + 25
            if frame_idx >= sub_start:
                sub_it = min(1.0, (frame_idx - sub_start) / 20.0)
                sub_y_off = (1.0 - sub_it) * 15 # slide up by 15px
                
                sub_text = "Event-Driven Agent Orchestration"
                sbbox = font_ichno_sub.getbbox(sub_text)
                sw = sbbox[2] - sbbox[0]
                sx = (width - sw) // 2
                sy = iy + ih + 44 + sub_y_off
                
                # Subtitle cyan glow
                odraw.text((sx - 1, sy), sub_text, font=font_ichno_sub, fill=(56, 189, 248, int(90 * sub_it)))
                odraw.text((sx + 1, sy), sub_text, font=font_ichno_sub, fill=(56, 189, 248, int(90 * sub_it)))
                odraw.text((sx, sy), sub_text, font=font_ichno_sub, fill=(225, 245, 255, int(255 * sub_it)))

            # Bottom badge tag
            badge_start = ichno_start + 40
            if frame_idx >= badge_start:
                badge_t = min(1.0, (frame_idx - badge_start) / 20.0)
                badge_text = "DETERMINISTIC CODE BLAME  •  BOUNDED LLM EXPLANATION  •  HUMAN SIGN-OFF"
                bb_box = font_badge.getbbox(badge_text)
                bw = bb_box[2] - bb_box[0]
                bx = (width - bw) // 2
                by_pos = height - 90
                
                # Badge pill background
                pad_x = 24
                pad_y = 8
                pill_rect = [(bx - pad_x, by_pos - pad_y), (bx + bw + pad_x, by_pos + (bb_box[3] - bb_box[1]) + pad_y)]
                odraw.rounded_rectangle(pill_rect, radius=8, fill=(18, 24, 38, int(220 * badge_t)), outline=(60, 80, 120, int(150 * badge_t)), width=1)
                odraw.text((bx, by_pos), badge_text, font=font_badge, fill=(130, 180, 230, int(230 * badge_t)))

            # Composite PIL overlay back
            img_rgba = Image.fromarray(cv2.cvtColor(frame_cv, cv2.COLOR_BGR2RGBA))
            img_rgba = Image.alpha_composite(img_rgba, overlay)
            frame_cv = cv2.cvtColor(np.array(img_rgba), cv2.COLOR_RGBA2BGR)

        # Save frame to disk
        frame_path = os.path.join(temp_dir, f"frame_{frame_idx:04d}.png")
        cv2.imwrite(frame_path, frame_cv)

    print("Frames successfully rendered.")
    
    # Encode with FFmpeg
    output_mp4 = "d:/Ichnoscope-WCC-30/docs/assets/ichnoscope-motion-graphic.mp4"
    output_gif = "d:/Ichnoscope-WCC-30/docs/assets/ichnoscope-motion-graphic.gif"
    
    # 1. Render MP4
    print("Encoding MP4 video via FFmpeg...")
    ffmpeg_mp4_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(temp_dir, "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "medium",
        output_mp4
    ]
    subprocess.run(ffmpeg_mp4_cmd, check=True)
    print(f"MP4 saved to {output_mp4}")
    
    # 2. Render high quality GIF with palettegen & paletteuse
    print("Encoding high-quality GIF via FFmpeg...")
    palette_path = os.path.join(temp_dir, "palette.png")
    
    # Generate custom palette
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(temp_dir, "frame_%04d.png"),
        "-vf", "fps=20,scale=960:-1:flags=lanczos,palettegen=stats_mode=diff",
        palette_path
    ], check=True)
    
    # Use palette to generate smooth GIF
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(temp_dir, "frame_%04d.png"),
        "-i", palette_path,
        "-lavfi", "fps=20,scale=960:-1:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=3",
        output_gif
    ], check=True)
    print(f"GIF saved to {output_gif}")

if __name__ == "__main__":
    create_motion_graphic()
