import gradio as gr
# import spaces
import math

"""
                                         PipeIQ
"""

# @spaces.GPU
def qv2d(q,v):
  if q == 0:
    raise gr.Warning("Enter non-zero value of flow rate!",duration=5)
  q=q/3600 # m3/hr to m3/s
  if v == 0:
    raise gr.Warning("Enter non-zero value of velocity!",duration=5)
  a=q/v # cross-section area
  r2=a/math.pi
  r=math.sqrt(r2)
  d=2*r
  fn = v/(math.sqrt(d*9.81))
  warn = "This version does not contain design warnings."
  return """
  internal diameter is {} mm
  Comments:
  {}
  """.format(round(d*1000,2),warn)

with gr.Blocks() as QV2D:
  with gr.Row():
    q=gr.Number(label="Volumetric flow rate (m3/hr)",minimum=0)
    v=gr.Number(label="Velocity (m/s)",minimum=0,value=2)
  output = gr.Textbox(label="Result: Diameter (mm)")
  calc_btn1 = gr.Button("Run")
  calc_btn1.click(
        fn=qv2d,
        inputs=[q,v],
        outputs = output
  )

import pandas as pd
pipeRoughness = pd.read_csv("pipeRoughness.csv")

# @spaces.GPU
def hydraulics(q,d,spgr,mu,moc,l,h_suc,h_dis,h_eqp,
               n_gl_convention,n_ga,
               n_tee_branch,n_bend_90,n_bend_45,
               hyd_eff,m_eff,
			   pipe_loc,liq_state):
  # Unit conversions:
  if q == 0:
    raise gr.Warning("Enter non-zero value of flow rate!",duration=5)
  q = q/3600 # m3/hr to m3/s
  if d == 0:
    raise gr.Warning("Enter non-zero value of Internal Diameter!",duration=5)
  d = d/1000 # mm to m
  if mu == 0:
    raise gr.Warning("Enter non-zero value of viscosity!",duration=5)
  mu = mu/1000 # cP to Pa-s
  # cross-section area in m2
  a = 0.25*(math.pi)*math.pow(d,2)
  # velocity in m/s
  v = q/a
  # Density in kg/m3
  if spgr == 0:
    raise gr.Warning("Enter non-zero value of SPGR!",duration=5)
  rho = spgr*1000
  # reynold's number
  re = (rho*v*d)/mu
  # froude number
  fn = v/(math.sqrt(d*9.81))
  warn = "This version does not include design warnings."
  pr = 0 # pipe roughness in mm (NORSOK & Mc Graw Hill)
  pr = float(pipeRoughness.loc[pipeRoughness["moc"] == moc, "pr"].iloc[0])
  # pipe roughness in m
  pr = pr / 1000
  # relative pipe roughness
  rpr = pr / d
  # friction factor for laminar flow regime
  if re < 2100:
    f = 64 / re # friction factor
  else:
    # swamee-jain equation for darcy's friction factor
    t1 = rpr / 3.7
    t2 = 5.74 / math.pow(re, 0.9)
    t3 = t1 + t2
    t4 = math.pow(math.log10(t3), 2)
    f = 0.25 / t4 # friction factor
  # minor losses (US DOE), equivalent length = (quantity)*(factor)*(diameter)
  l_gl_convention = n_gl_convention*400*d
  l_ga = n_ga*10*d
  l_tee_branch = n_tee_branch*60*d
  l_bend_90 = n_bend_90*30*d
  l_bend_45 = n_bend_45*16*d
  # net length = length + equivalent lengths
  l = l+l_gl_convention+l_ga
  l = l+l_tee_branch+l_bend_90+l_bend_45
  # darcy's equation (headloss in m)
  h = (f*(l/d)*math.pow(v,2))/(2*9.81)
  # total head
  h = h+h_dis-h_suc+h_eqp
  # pressure in Pa
  p = h*9.81*rho
  # pressure in Bar
  p_bar = p/100000
  p_bar = round(p_bar,2)
  # power calculation
  hyd_power = q*p # hydraulic power
  if hyd_eff == 0:
    raise gr.Warning("Enter non-zero value of hydraulic efficiency!",duration=5)
  pump_power = hyd_power/hyd_eff # pump power (motor output power)
  if m_eff == 0:
    raise gr.Warning("Enter non-zero value of motor efficiency!",duration=5)
  m_power = pump_power/m_eff # motor power
  return """
  Velocity: {} m/s
  Headloss: {} m
  Pressure: {} Bar
  Hydraulic power: {} W
  Pump power (motor output): {} W
  Motor power (motor input): {} W
  Comments:
  {}
  """.format(round(v,2),
             round(h,3),
             p_bar,
             round(hyd_power,2),
             round(pump_power,2),
             round(m_power,2),
             warn)

with gr.Blocks() as Hydraulics:
  gr.Markdown("Flow, Length, Density, MOC, Diameter, & Viscosity (mandatory)")
  with gr.Row():
    q = gr.Number(label="Volumetric flow rate (m3/hr)", minimum=0)
    l = gr.Number(label="Pipeline length (m)", minimum=0, value=1)
  with gr.Row():
    spgr = gr.Number(label="Specific Gravity (e.g. 1 for water)", minimum=0, value=1)
    moc = gr.Dropdown(pipeRoughness["moc"].tolist(), label="MOC")
    # moc = gr.Dropdown(["CS, non-corroded", "CS, corroded", "SS", "Ti/Cu-Ni", "GRP", "PVC", "Steel carcass", "Generic Polymer",
				# 	   "CI","GI","WI","Concrete (max resistance)","PVC / Drawn Tubing / Glass","Asphalted CI","Riveted Steel (max resistance)"], label="MOC")
  with gr.Row():
    d = gr.Number(label="I.D. (Internal Diameter) (mm)", minimum=0)
    mu = gr.Number(label="Viscosity (cP)", minimum=0, value=1)
  gr.Markdown("Heads (recommended, but not mandatory if only total frictional loss is required)")
  with gr.Row():
    h_suc = gr.Number(label="Suction head (m)", minimum=0)
    h_dis = gr.Number(label="Discharge head (m)", minimum=0)
    h_eqp = gr.Number(label="Equipment head loss (m)", minimum=0)
  gr.Markdown("Valves & Fittings (recommended if total frictional loss is required, but not mandatory)")
  with gr.Row():
    n_gl_convention = gr.Number(label="No. of globe valves", minimum=0)
    n_ga = gr.Number(label="No. of gate valves (100% open)", minimum=0)
  with gr.Row():
    n_tee_branch = gr.Number(label="No. of tee branchs", minimum=0)
    n_bend_90 = gr.Number(label="No. of bend 90 degree bends", minimum=0)
    n_bend_45 = gr.Number(label="No. of bend 45 degree bends", minimum=0)
  gr.Markdown("Efficiencies from datasheets (recommended, but not mandatory)")
  with gr.Row():
    hyd_eff = gr.Number(label="Hydraulic efficiency", minimum=0, value=0.6, maximum=1)
    m_eff = gr.Number(label="Motor efficiency", minimum=0, value=0.8, maximum=1)
  gr.Markdown("Additional details for rating the pipeline (recommended, but not mandatory)")
  with gr.Row():
    pipe_loc = gr.Dropdown(["Discharge", "Suction"], label="Pipe Location")
    liq_state = gr.Dropdown(["Sub-Cooled", "Boiling"], label="Liquid State (only for suction)")
  # gr.Markdown("Click on the Run button below")
  output = gr.Textbox(
    label="Result: Headloss & Power Calculation"
  )
  calc_btn1 = gr.Button("Run")
  calc_btn1.click(
    fn = hydraulics,
    inputs = [q,d,spgr,mu,moc,l,h_suc,h_dis,h_eqp,
              n_gl_convention,n_ga,
              n_tee_branch,n_bend_90,n_bend_45,
              hyd_eff,m_eff,
			  pipe_loc,liq_state],
    outputs = output
  )

# minimum thickness for structural integrety removed from free version

# @spaces.GPU
def ca(mca,dl,cr):
    # NORSOK standard
    if cr <= 0:
      raise gr.Info("Corrosion rate should be more than 0!",duration=5)
    tca = mca + ((dl-5)*cr)
    warn = "This version does not include design warnings."
    return """
    Corrosion allowance: {} mm
    Comment:
    {}
    """.format(round(tca,2),warn)

with gr.Blocks() as CA:
  gr.Markdown("Corrosion Allowance")
  with gr.Row():
    mca = gr.Number(label="Minimum Corrosion Allowance (mm) (do not change the default value unless necessary)", minimum=0, value=2)
    dl = gr.Number(label="Design Life (years)", minimum=5)
    cr = gr.Number(label="Corrosion Rate (mm/year) (do not change the default value unless necessary)", minimum=0, value=0.4)
  output = gr.Textbox(label="Result: Pipe Thickness (mm)")
  calc_btn1 = gr.Button("Run")
  calc_btn1.click(
    fn=ca,
    inputs=[mca,dl,cr],
    outputs=output
  )

import pandas as pd

# Load the CSV/Excel data once when the application starts
# pc = pd.read_csv("pipeClass.csv")

# pipe class removed from free version

with gr.Blocks() as PipeIQ:
    gr.Markdown("# Continuity")
    QV2D.render()
    gr.Markdown("# Headloss")
    Hydraulics.render()
    gr.Markdown("# Corrosion Allowance")
    CA.render()

# new tab begins

"""
                                         PumpIQ
"""

# @spaces.GPU
def npsha(pa,h,spgr,pf,psat):
  ph = ((1000*spgr)*9.81*h)/100000
  if pa+ph-pf-psat <= 0:
    raise gr.Error("NPSHa should be more than 0!",duration=5)
  return "NPSH Available: {} m @ SPGR: {}".format(round(((pa+ph-pf-psat)*100000)/(1000*spgr*9.81),2),spgr)

with gr.Blocks() as NPSHa:
  pa = gr.Number(label="Absolute pressure on the surface of the liquid (Bar) (do not change the default value unless necessary)",
                   minimum=0, value=1.01325)
    # with gr.Row():
  h = gr.Number(label="Elevation (m)", value=0)
  spgr = gr.Number(label="Specific Gravity", minimum=0, value=1)
    # with gr.Row():
  pf = gr.Number(label="Frictional loss (Bar)", minimum=0)
  psat = gr.Number(label="Saturation pressure (Bar) (do not change the default value unless necessary)", minimum=0, value=0.1)
  output = gr.Textbox(label="Result: NPSHa")
  calc_btn1 = gr.Button("Run")
  calc_btn1.click(
    fn=npsha,
    inputs=[pa,h,spgr,pf,psat],
    outputs=output
  )

# @spaces.GPU
def scaleFlowByDia(q1,q2,d1,h1,m1):
  if q1 == 0:
    raise gr.Error("Old flow cannot be 0!")
  if q2 == 0:
    raise gr.Info("New flow shouldn't be 0!")
  if d1 == 0:
    raise gr.Warning("Old impeller diameter shouldn't be 0!")
  if h1 == 0:
    raise gr.Warning("Old head shouldn't be 0!")
  if m1 == 0:
    raise gr.Warning("Old power requirement shouldn't be 0!")
  d2 = round(d1*math.pow(q2/q1,1),2)
  h2 = round(h1*math.pow(q2/q1,2),2)
  m2 = round(m1*math.pow(q2/q1,3),2)
  return """
  revised diameter: {}
  revised head: {}
  revised power requirement (not necessarily equal to motor power): {}
  Note: speed (e.g. in RPM) is assumed to be constant.
  """.format(d2,h2,m2)

with gr.Blocks() as ScaleFlowByDiameter:
  gr.Markdown("Scaling flow by changing impeller diameter and possibly motor")
  with gr.Row():
    q1 = gr.Number(label="Old flow", minimum=0)
    q2 = gr.Number(label="New flow", minimum=0)
  with gr.Row():
    d1 = gr.Number(label="Old diameter", minimum=0)
    h1 = gr.Number(label="Old head", minimum=0)
    m1 = gr.Number(label="Old power requirement (not necessarily equal to motor power)", minimum=0)
  output = gr.Textbox(label="Scaling by changing impeller diameter")
  calc_btn1 = gr.Button("Run")
  calc_btn1.click(
    fn=scaleFlowByDia,
    inputs=[q1,q2,d1,h1,m1],
    outputs=output
  )

# @spaces.GPU
def scaleFlowByN(q1,q2,n1,h1,m1):
  if q1 == 0:
    raise gr.Error("Old flow cannot be 0!")
  if q2 == 0:
    raise gr.Info("New flow shouldn't be 0!")
  if n1 == 0:
    raise gr.Warning("Old speed shouldn't be 0!")
  if h1 == 0:
    raise gr.Warning("Old head shouldn't be 0!")
  if m1 == 0:
    raise gr.Warning("Old power requirement shouldn't be 0!")
  n2 = round(n1*math.pow(q2/q1,1),2)
  h2 = round(h1*math.pow(q2/q1,2),2)
  m2 = round(m1*math.pow(q2/q1,3),2)
  return """
  revised speed: {}
  revised head: {}
  revised power requirement (not necessarily equal to motor power): {}
  Note: impeller diameter is assumed to be constant.
  """.format(n2,h2,m2)

with gr.Blocks() as ScaleFlowBySpeed:
  gr.Markdown("Scaling flow by changing impeller diameter and possibly motor")
  with gr.Row():
    q1 = gr.Number(label="Old flow", minimum=0)
    q2 = gr.Number(label="New flow", minimum=0)
  with gr.Row():
    n1 = gr.Number(label="Old speed", minimum=0)
    h1 = gr.Number(label="Old head", minimum=0)
    m1 = gr.Number(label="Old power requirement (not necessarily equal to motor power)", minimum=0)
  output = gr.Textbox(label="Scaling by changing speed")
  calc_btn1 = gr.Button("Run")
  calc_btn1.click(
    fn=scaleFlowByN,
    inputs=[q1,q2,n1,h1,m1],
    outputs=output
  )

# electrical-related features removed from free version

with gr.Blocks() as PumpIQ:
    gr.Markdown("# NPSHa")
    NPSHa.render()
    gr.Markdown("# Pump Scaling")
    ScaleFlowByDiameter.render()
    ScaleFlowBySpeed.render()

# new tab begins

"""
                                         SteamIQ
"""

import pandas as pd

# steamTable = pd.read_csv("steamTable2.csv")
steamTableRaw = pd.read_csv("steamTableRaw.csv")

# steam line sizing feature removed from free version

# @spaces.GPU
def steam_table(p_bar):
  t = steamTableRaw.loc[steamTableRaw["Pressure"] == p_bar]["Temperature"]
  t = float(t.iloc[0])
  st_sp_vol = steamTableRaw.loc[steamTableRaw["Pressure"] == p_bar]["Specific Vapor Vol"]
  st_sp_vol = float(st_sp_vol.iloc[0])
  h_vap = steamTableRaw.loc[steamTableRaw["Pressure"] == p_bar]["h vapor"]
  h_vap = float(h_vap.iloc[0])
  h_w = steamTableRaw.loc[steamTableRaw["Pressure"] == p_bar]["h water"]
  h_w = float(h_w.iloc[0])
  return """
  Data corresponding to Saturated Steam:
  Temperature = {} ℃
  Specific Vapor Volume = {} m3/kg
  H - Vapor = {} kJ/kg
  H - Water = {} kJ/kg
  """.format(t,st_sp_vol,h_vap,h_w)

with gr.Blocks() as SteamTable:
  gr.Markdown()
  p_bar = gr.Dropdown(steamTableRaw["Pressure"].tolist(), label="Absolute Pressure (Bar)")
  output = gr.Textbox(label="Result: Saturated Steam Data")
  calc_btn1 = gr.Button("Run")
  calc_btn1.click(
    fn=steam_table,
    inputs=[p_bar],
    outputs=output
  )

with gr.Blocks() as SteamIQ:
    gr.Markdown("# Steam Table")
    SteamTable.render()

"""
                                         Extras
"""

# removed from free version

# all tabs end

"""
                                         App Launch
"""

# app launch

with gr.Blocks() as Blog:
    gr.Markdown("# Publicly available references")
    gr.Button(value="Steam Table (for FlowIQ)",link="https://sid.siemens.com/api/khub/documents/gS3b4wAMC~5gSw2cPHLRHg/content",link_target='_blank')
    gr.Button(value="MOC Compatibility Tables (for FlowIQ)",
              link="https://www.graco.com/content/dam/graco/com_documents/NPN/ipd/chemical-compatibility-guide/Graco_ChemCompGuideEN-D.pdf",link_target='_blank')
    gr.Button(value="Heat Transfer Coefficients (for HeatIQ)",
              link="https://onlinelibrary.wiley.com/doi/pdf/10.1002/9783527621583.app2",link_target='_blank')
    gr.Markdown("# Social Media")
    gr.Button(value="LinkedIn - Atrium Water",link="https://www.linkedin.com/company/atriumwater/",link_target='_blank')
    gr.Button(value="YouTube - Atrium Water",link="https://www.youtube.com/@atrium-water/",link_target='_blank')
    gr.Markdown("# Tables")
    gr.Markdown("Pipe Roughness")
    gr.DataFrame(value=pipeRoughness, interactive=False)
    gr.Markdown("Saturated Steam Data")
    gr.DataFrame(value=steamTableRaw, interactive=False)

app = gr.TabbedInterface([Blog,PipeIQ,PumpIQ,SteamIQ], ["FlowIQ Home","PipeIQ","PumpIQ","SteamIQ",], title = "FlowIQ")
app.launch(server_name="0.0.0.0", inbrowser=True, favicon_path="AtriumLogo.ico",
           theme=gr.themes.Soft(primary_hue = gr.themes.colors.emerald, secondary_hue = gr.themes.colors.red, neutral_hue = gr.themes.colors.stone))

