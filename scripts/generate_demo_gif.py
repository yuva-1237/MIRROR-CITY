import os
from PIL import Image, ImageDraw, ImageFont

def generate_walkthrough_gif():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_dir = os.path.join(base_dir, "..", "docs", "images")
    output_path = os.path.join(img_dir, "demo_walkthrough.gif")
    
    scenario_path = os.path.join(img_dir, "scenario_planner.png")
    dashboard_path = os.path.join(img_dir, "dashboard_3d.png")
    
    base_scenario = Image.open(scenario_path).convert("RGBA")
    base_dashboard = Image.open(dashboard_path).convert("RGBA")
    
    W, H = base_scenario.size # 1024 x 576
    
    # Fonts
    font_title = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 22)
    font_bold = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 15)
    font_reg = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 13)
    font_sm = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 11)
    font_val = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 18)
    
    frames = []
    
    # Color palette
    c_bg_card = (13, 19, 34, 235)
    c_border_card = (51, 65, 85, 255)
    c_blue = (59, 130, 246, 255)
    c_cyan = (6, 182, 212, 255)
    c_emerald = (16, 185, 129, 255)
    c_amber = (245, 158, 11, 255)
    c_red = (239, 68, 68, 255)
    c_text_white = (255, 255, 255, 255)
    c_text_dim = (148, 163, 184, 255)
    
    def draw_banner(draw, step_num, step_title, step_desc, progress_pct):
        # Top banner
        draw.rectangle([(0, 0), (W, 48)], fill=(9, 13, 22, 245))
        draw.line([(0, 48), (W, 48)], fill=(30, 41, 59, 255), width=2)
        
        # Step tag
        tag_text = f"STEP {step_num}/4"
        draw.rounded_rectangle([(16, 10), (95, 38)], radius=6, fill=c_blue)
        draw.text((25, 14), tag_text, font=font_bold, fill=c_text_white)
        
        # Title
        draw.text((108, 12), step_title, font=font_bold, fill=c_text_white)
        draw.text((360, 15), f"|  {step_desc}", font=font_reg, fill=c_text_dim)
        
        # Progress bar at very top
        draw.rectangle([(0, 0), (W, 4)], fill=(30, 41, 59, 255))
        draw.rectangle([(0, 0), (int(W * progress_pct), 4)], fill=c_cyan)
        
    # --- STAGE 1: ADD HOSPITAL (Frames 0-3) ---
    for i in range(4):
        im = base_scenario.copy()
        draw = ImageDraw.Draw(im)
        
        progress = 0.05 + (i * 0.05)
        draw_banner(draw, 1, "Add Infrastructure", "Placing 'Saint Jude Regional Hospital' on City Grid", progress)
        
        # Tool Palette Highlight
        draw.rounded_rectangle([(24, 75), (280, 165)], radius=8, fill=c_bg_card, outline=c_blue, width=2)
        draw.text((36, 85), "ACTIVE INFRASTRUCTURE TOOL", font=font_sm, fill=c_cyan)
        draw.text((36, 102), "🏥 Hospital Placement", font=font_bold, fill=c_text_white)
        draw.text((36, 124), "Radius: 1,500m  •  Capacity: 500 beds", font=font_reg, fill=c_text_dim)
        draw.text((36, 142), "Estimated Capital Cost: $120,000,000", font=font_reg, fill=c_amber)
        
        # Hospital marker on map with pulse ring
        pulse_r = 28 + (i * 6)
        draw.ellipse([(580 - pulse_r, 260 - pulse_r), (580 + pulse_r, 260 + pulse_r)], outline=(239, 68, 68, 120), width=2)
        draw.ellipse([(580 - 20, 260 - 20), (580 + 20, 260 + 20)], fill=c_red, outline=c_text_white, width=2)
        draw.text((571, 248), "+", font=font_title, fill=c_text_white)
        
        # Map tooltip
        draw.rounded_rectangle([(610, 240), (840, 290)], radius=6, fill=c_bg_card, outline=c_border_card)
        draw.text((620, 246), "St. Jude Hospital Added", font=font_bold, fill=c_text_white)
        draw.text((620, 266), "Zoning: Commercial Corridor (Node 2,2)", font=font_sm, fill=c_text_dim)
        
        frames.append(im.convert("RGB"))
        
    # --- STAGE 2: RECALCULATE SIMULATION (Frames 4-7) ---
    for i in range(4):
        im = base_scenario.copy()
        draw = ImageDraw.Draw(im)
        
        progress = 0.25 + (i * 0.06)
        draw_banner(draw, 2, "Recalculate Simulation", "Executing Spectral Graph Propagation & Multi-Agent Loop", progress)
        
        # Keep hospital marker
        draw.ellipse([(580 - 18, 260 - 18), (580 + 18, 260 + 18)], fill=c_red, outline=c_text_white, width=2)
        draw.text((571, 248), "+", font=font_title, fill=c_text_white)
        
        # Glowing Action Button
        draw.rounded_rectangle([(320, 180), (704, 250)], radius=12, fill=(17, 24, 39, 250), outline=c_cyan, width=3)
        draw.text((345, 195), "⚡ RUNNING DIGITAL TWIN SIMULATION", font=font_bold, fill=c_cyan)
        calc_steps = [
            "1/3 Building normalized Laplacian matrix A_tilde...",
            "2/3 Spectral propagation: H^(l+1) = D^-0.5 A_tilde D^-0.5 H W...",
            "3/3 Multi-agent collaboration cycle (10 AI agents)...",
            "Synthesizing cross-domain city metrics..."
        ]
        draw.text((345, 222), calc_steps[i], font=font_reg, fill=c_text_white)
        
        # Bottom status pill
        draw.rounded_rectangle([(360, 520), (664, 555)], radius=20, fill=(30, 41, 59, 240), outline=c_blue)
        draw.text((385, 528), "⚙️ Engine: SpectralTrafficPropagator.py", font=font_bold, fill=c_cyan)
        
        frames.append(im.convert("RGB"))

    # --- STAGE 3: METRICS CHANGE (Frames 8-11) ---
    for i in range(4):
        im = base_dashboard.copy()
        draw = ImageDraw.Draw(im)
        
        progress = 0.50 + (i * 0.06)
        draw_banner(draw, 3, "Metrics Recalculated", "Comparing Baseline vs. Proposed Scenario Outcomes", progress)
        
        # Metrics Overlay Dashboard Card
        draw.rounded_rectangle([(40, 70), (984, 185)], radius=10, fill=c_bg_card, outline=c_border_card, width=2)
        draw.text((60, 80), "SIMULATION IMPACT DELTAS (POST-RECALCULATION)", font=font_bold, fill=c_text_white)
        
        # Metric 1: Healthcare Coverage
        draw.rounded_rectangle([(60, 105), (275, 170)], radius=6, fill=(15, 23, 42, 220), outline=c_emerald)
        draw.text((72, 112), "HEALTHCARE COVERAGE", font=font_sm, fill=c_text_dim)
        draw.text((72, 130), "78.6%", font=font_val, fill=c_emerald)
        draw.text((140, 134), "+24.4% ↑", font=font_bold, fill=c_emerald)
        draw.text((72, 152), "Baseline: 54.2%", font=font_sm, fill=c_text_dim)
        
        # Metric 2: 8-Min Response Radius
        draw.rounded_rectangle([(290, 105), (505, 170)], radius=6, fill=(15, 23, 42, 220), outline=c_emerald)
        draw.text((302, 112), "TRAUMA 8-MIN RADIUS", font=font_sm, fill=c_text_dim)
        draw.text((302, 130), "2,450m", font=font_val, fill=c_emerald)
        draw.text((385, 134), "+104% ↑", font=font_bold, fill=c_emerald)
        draw.text((302, 152), "Baseline: 1,200m", font=font_sm, fill=c_text_dim)
        
        # Metric 3: Traffic Congestion (Spectral graph propagation)
        draw.rounded_rectangle([(520, 105), (735, 170)], radius=6, fill=(15, 23, 42, 220), outline=c_cyan)
        draw.text((532, 112), "CONGESTION INDEX", font=font_sm, fill=c_text_dim)
        draw.text((532, 130), "59.1%", font=font_val, fill=c_cyan)
        draw.text((595, 134), "-9.3% ↓", font=font_bold, fill=c_cyan)
        draw.text((532, 152), "Via Spectral Propagation", font=font_sm, fill=c_text_dim)
        
        # Metric 4: Capital Budget
        draw.rounded_rectangle([(750, 105), (965, 170)], radius=6, fill=(15, 23, 42, 220), outline=c_amber)
        draw.text((762, 112), "CAPITAL INVESTMENT", font=font_sm, fill=c_text_dim)
        draw.text((762, 130), "$120.0M", font=font_val, fill=c_amber)
        draw.text((845, 134), "Approved", font=font_bold, fill=c_text_dim)
        draw.text((762, 152), "Feasibility: High", font=font_sm, fill=c_emerald)
        
        frames.append(im.convert("RGB"))

    # --- STAGE 4: AGENT ADVISORY (Frames 12-15) ---
    for i in range(4):
        im = base_dashboard.copy()
        draw = ImageDraw.Draw(im)
        
        progress = 0.75 + (i * 0.06)
        draw_banner(draw, 4, "AI Agent Advisory", "Multi-Agent Core Issues Actionable Municipal Analysis", progress)
        
        # Agent Advisory Card 1: Healthcare Agent
        draw.rounded_rectangle([(40, 70), (500, 240)], radius=10, fill=c_bg_card, outline=c_emerald, width=2)
        draw.text((55, 80), "🩺 HEALTHCARE AI AGENT", font=font_bold, fill=c_emerald)
        draw.text((360, 82), "CONFIDENCE: 98.4%", font=font_sm, fill=c_cyan)
        draw.line([(55, 102), (485, 102)], fill=(30, 41, 59, 255), width=1)
        draw.text((55, 112), "RECOMMENDATION: APPROVE PROPOSAL", font=font_bold, fill=c_text_white)
        draw.text((55, 135), "• Placement eliminates critical trauma blindspot across eastern sector.", font=font_reg, fill=c_text_white)
        draw.text((55, 155), "• Bed capacity (+500) accommodates projected 10-year district growth.", font=font_reg, fill=c_text_white)
        draw.text((55, 175), "• Reduces ambulance emergency transfer latency from 14.2m to 6.8m.", font=font_reg, fill=c_emerald)
        draw.text((55, 205), "Cross-Domain Impact: Citizen Wellness score +18.2 pts", font=font_bold, fill=c_cyan)
        
        # Agent Advisory Card 2: Traffic Flow Agent
        draw.rounded_rectangle([(520, 70), (984, 240)], radius=10, fill=c_bg_card, outline=c_blue, width=2)
        draw.text((535, 80), "🚗 TRAFFIC FLOW AI AGENT", font=font_bold, fill=c_blue)
        draw.text((840, 82), "CONFIDENCE: 95.1%", font=font_sm, fill=c_cyan)
        draw.line([(535, 102), (965, 102)], fill=(30, 41, 59, 255), width=1)
        draw.text((535, 112), "CORRIDOR CONGESTION ASSESSMENT", font=font_bold, fill=c_text_white)
        draw.text((535, 135), "• Spectral propagation models indicate adjacent feeder roads remain <0.62.", font=font_reg, fill=c_text_white)
        draw.text((535, 155), "• Recommend synchronizing signal timings on North-South Ave 2 & 3.", font=font_reg, fill=c_text_white)
        draw.text((535, 175), "• Net commuting travel times decrease across 4 out of 6 zones.", font=font_reg, fill=c_emerald)
        draw.text((535, 205), "Advisory Verdict: Feasible without additional road widening", font=font_bold, fill=c_emerald)
        
        # Bottom summary strip
        draw.rounded_rectangle([(40, 490), (984, 550)], radius=8, fill=(15, 23, 42, 240), outline=c_border_card)
        draw.text((60, 502), "EXECUTIVE SUMMARY FOR CITY PLANNERS", font=font_bold, fill=c_text_white)
        draw.text((60, 524), "Add Hospital ➔ Recalculate Simulation ➔ Metrics Update (+24% Coverage) ➔ Agent Advisory Verified", font=font_reg, fill=c_cyan)
        
        frames.append(im.convert("RGB"))
        
    # Save animated GIF
    # Durations: 1200ms per frame to make it easily readable and cinematic
    durations = [1200] * len(frames)
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"Generated walkthrough GIF at: {output_path} ({len(frames)} frames)")

if __name__ == "__main__":
    generate_walkthrough_gif()
