# build_room.rb — INTERIOR-AI NATIVE SketchUp generator  (the "editable channel").
#
# WHY THIS EXISTS: exporting Blender geometry into SketchUp arrives as triangle
# soup (non-editable). The fix that opens the editable-deliverable channel is to
# NOT export geometry at all — ship THIS generated Ruby script. The collaborator
# runs it inside her licensed desktop SketchUp and gets FULLY NATIVE, EDITABLE
# geometry (real Faces, push/pulled solids, named Groups on Tags) built from the
# SAME spec that clearance_check.py validated. We generate the script (token-rich
# advantage); she runs it (one line).
#
# HOW SHE RUNS IT (needs SketchUp Pro DESKTOP; the free WEB version can't run Ruby):
#   Window > Ruby Console, then:   load 'C:/path/to/build_room.rb'
#   (optionally point at a spec first:  $INTERIOR_SPEC = 'C:/path/to/specs/living_demo.json')
#
# SketchUp's internal length unit is INCHES, so the spec's inch coordinates map 1:1.
# A room-spec@0.2 (metric, "outline_mm") is auto-detected and converted mm -> inch; it
# builds an L-shaped POLYGON shell + ensuite sub-room + built-in millwork (build_suite).
#
# STATUS: candidate route — being validated by the 2026-06-30 interop research. The v0.1
# rectangular path is unchanged; the v0.2 polygon path is NEW and NOT yet smoke-tested in
# real SketchUp (no SketchUp on the build machine) -> the friend runs FOR-FRIEND.md first.
# Verify against the live SketchUp Ruby API before any client deliverable.

require 'json'

module InteriorAI
  MM_TO_IN = 1.0 / 25.4
  # Mirrors pipeline/specs/living_demo.json (used if no spec file is provided).
  DEFAULT_SPEC = {
    "room" => { "type" => "living", "width_in" => 168, "depth_in" => 192, "ceiling_in" => 96,
                "wall_thk_in" => 4.5, "floor_thk_in" => 4.0,
                "door" => { "w_in" => 32, "h_in" => 80, "wall" => "south" } },
    "items" => [
      { "name" => "sofa", "kind" => "sofa", "x" => 24, "y" => 12, "w" => 84, "d" => 36, "h" => 34 },
      { "name" => "coffee table", "kind" => "coffee_table", "x" => 45, "y" => 64, "w" => 42, "d" => 22, "h" => 18 }
    ]
  }

  def self.load_spec
    path = defined?($INTERIOR_SPEC) ? $INTERIOR_SPEC : nil
    return DEFAULT_SPEC if path.nil? || !File.exist?(path)
    JSON.parse(File.read(path))
  end

  # Axis-aligned box as a NATIVE editable Group: one planar face + push/pull.
  # Coordinates are inches (SketchUp's internal unit).
  def self.box(parent, name, x, y, z, w, d, h, tag = nil)
    # Skip degenerate boxes (zero/negative size from a bad or missing spec value).
    # add_face returns nil on a zero-area outline; calling .normal on nil would
    # crash, and the rescue would abort the WHOLE model -> friend gets nothing.
    if w <= 0 || d <= 0 || h <= 0
      puts "InteriorAI: skipped '#{name}' (bad size w=#{w} d=#{d} h=#{h})"
      return nil
    end
    grp  = parent.add_group
    ents = grp.entities
    pts  = [[x, y, z], [x + w, y, z], [x + w, y + d, z], [x, y + d, z]]
    face = ents.add_face(pts.map { |p| Geom::Point3d.new(p[0], p[1], p[2]) })
    unless face
      grp.erase! if grp.valid?
      puts "InteriorAI: skipped '#{name}' (degenerate outline)"
      return nil
    end
    face.reverse! if face.normal.z < 0     # push/pull "up" regardless of winding
    face.pushpull(h)
    grp.name = name
    grp.layer = tag if tag                  # Layer == Tag in modern SketchUp
    grp
  end

  # --- furniture component catalog (the friend's real SketchUp models) ----------
  # Catalog JSON maps a furniture KIND -> a .skp component file, e.g.
  #   { "sofa": {"file": "sofas/boucle_3seat.skp"}, "dining_chair": {"file": "chair.skp"} }
  # Point $INTERIOR_CATALOG at it, or drop furniture_catalog.json next to this script.
  # Paths inside the catalog are resolved relative to the catalog file. Any kind not
  # mapped (or missing file) falls back to a primitive box.
  def self.load_catalog
    path = defined?($INTERIOR_CATALOG) ? $INTERIOR_CATALOG : nil
    path ||= File.join(File.dirname(__FILE__), "furniture_catalog.json")
    return {} unless path && File.exist?(path)
    { "dir" => File.dirname(path), "map" => JSON.parse(File.read(path)) }
  rescue => e
    puts "InteriorAI: catalog load failed (#{e.message}) -> box primitives"
    {}
  end

  # Licenses cleared for CLIENT deliverables (see docs/LICENSING.md). Anything else
  # (BIMobject / CADENAS-PARTcommunity / Hafele-via-those-routes / unknown) is
  # personal-use-only and must NOT ship in a client scene.
  PERMISSIVE_LICENSES = ["furnimesh", "3dwarehouse-combined", "original", "cc0", "commercial-ok"].freeze

  # Place the catalog component for an item at NATIVE size, footprint SW corner at
  # (x, y), sitting on the floor. Returns true if placed, false to fall back to a box.
  def self.place_component(ents, catalog, it, tag)
    return false if catalog.empty? || catalog["map"].nil?
    entry = catalog["map"][it["kind"]]
    return false if entry.nil?
    file = entry.is_a?(Hash) ? entry["file"] : entry
    return false if file.nil?
    abspath = File.expand_path(file.to_s, catalog["dir"])
    unless File.exist?(abspath)
      puts "InteriorAI: catalog file missing for '#{it['kind']}' (#{abspath}) -> box"
      return false
    end

    # Provenance / license gate (the founder has real liability exposure).
    if entry.is_a?(Hash)
      lic = (entry["license"] || "").to_s.downcase
      src = (entry["source"] || "unknown").to_s
      unless PERMISSIVE_LICENSES.include?(lic)
        puts "InteriorAI: !! LICENSE WARNING '#{it['kind']}' source=#{src} " \
             "license=#{lic.empty? ? 'MISSING' : lic} -- may NOT be client-deliverable; verify before shipping"
      end
    end

    defn = Sketchup.active_model.definitions.load(abspath)   # reuses the def if already loaded
    b = defn.bounds
    bw = b.width.to_f
    bd = b.height.to_f
    sw = it["w"].to_f
    sd = it["d"].to_f
    x = it["x"].to_f
    y = it["y"].to_f
    if entry.is_a?(Hash) && entry["fit"] && bw > 0 && bd > 0
      # SCALE the component to the dimensionally-correct spec footprint. Use for
      # inaccurate / AI-generated models whose native size is not authoritative —
      # this keeps OUR dimensions authoritative (the model is visual-only).
      bh = b.depth.to_f
      sx = sw / bw
      sy = sd / bd
      sz = bh > 0 ? [it["h"].to_f, 0.1].max / bh : 1.0
      tr = Geom::Transformation.translation(
             Geom::Vector3d.new(x - b.min.x * sx, y - b.min.y * sy, -b.min.z * sz)) *
           Geom::Transformation.scaling(sx, sy, sz)
      puts "InteriorAI: fit '#{it['name']}' -> #{sw.round}x#{sd.round}in"
    else
      # Place at the component's NATIVE size (correct for the friend's accurate
      # components). Flag if native size is far from spec -> set "fit": true or fix units.
      if sw > 0 && sd > 0 && (bw < sw * 0.5 || bw > sw * 1.5 || bd < sd * 0.5 || bd > sd * 1.5)
        puts "InteriorAI: !! SCALE WARNING '#{it['name']}' model #{bw.round}x#{bd.round}in " \
             "vs spec #{sw.round}x#{sd.round}in -- set \"fit\": true or check units"
      end
      tr = Geom::Transformation.new(Geom::Point3d.new(x - b.min.x, y - b.min.y, 0 - b.min.z))
    end
    inst = ents.add_instance(defn, tr)
    inst.name = "item: #{it['name']}"
    inst.layer = tag if tag
    puts "InteriorAI: placed '#{it['name']}' from #{File.basename(abspath)} (#{bw.round}x#{bd.round}in)"
    true
  rescue => e
    puts "InteriorAI: place failed for '#{it['name']}' (#{e.message}) -> box"
    false
  end

  # -------------------------------------------------------------------------------
  # DISPATCH: a room-spec@0.2 (metric polygon, "outline_mm") -> build_suite;
  # the classic room-spec@0.1 (rectangular, "width_in") -> build_rect (unchanged).
  def self.build
    spec = load_spec
    if spec["room"] && spec["room"]["outline_mm"]
      build_suite(spec)
    else
      build_rect(spec)
    end
  end

  # ---- v0.2 metric-polygon helpers ----------------------------------------------
  def self.signed_area(poly)   # poly = [[x,y],...] in inches; >0 => CCW
    a = 0.0
    n = poly.length
    n.times do |i|
      x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
      a += x1 * y2 - x2 * y1
    end
    a / 2.0
  end

  # Polygon floor slab: outline face at z=0, push/pulled DOWN by fth.
  def self.poly_floor(ents, name, outline_in, fth, tag)
    grp = ents.add_group
    face = grp.entities.add_face(outline_in.map { |p| Geom::Point3d.new(p[0], p[1], 0) })
    unless face
      grp.erase! if grp.valid?
      puts "InteriorAI: floor skipped (degenerate outline)"
      return nil
    end
    face.reverse! if face.normal.z < 0
    face.pushpull(-fth)        # extrude downward -> slab from -fth to 0
    grp.name = name; grp.layer = tag if tag
    grp
  rescue => e
    puts "InteriorAI: floor failed (#{e.message})"
    nil
  end

  # One straight wall segment along an edge: param range [ua,ub] on the edge line
  # (origin p1, unit direction adir), extruded OUTWARD by thk and UP by `height`
  # starting at z=z0. Used whole for a plain wall, or in pieces to leave a door gap.
  def self.wall_seg(ents, name, p1, adir, ua, ub, outward, thk, height, z0, tag)
    return nil if (ub - ua) <= 0.01 || height <= 0.01
    sx = p1[0] + adir[0] * ua; sy = p1[1] + adir[1] * ua
    ex = p1[0] + adir[0] * ub; ey = p1[1] + adir[1] * ub
    quad = [[sx, sy, z0], [ex, ey, z0],
            [ex + outward[0] * thk, ey + outward[1] * thk, z0],
            [sx + outward[0] * thk, sy + outward[1] * thk, z0]]
    grp = ents.add_group
    face = grp.entities.add_face(quad.map { |p| Geom::Point3d.new(p[0], p[1], p[2]) })
    unless face
      grp.erase! if grp.valid?
      puts "InteriorAI: wall '#{name}' skipped (degenerate)"
      return nil
    end
    face.reverse! if face.normal.z < 0
    face.pushpull(height)
    grp.name = name; grp.layer = tag if tag
    grp
  rescue => e
    puts "InteriorAI: wall '#{name}' failed (#{e.message})"
    nil
  end

  # If `door` sits on this edge, return [u0, u1, door_height_in] to leave a gap; else nil.
  def self.door_on_edge(door, p1, adir, len)
    return nil unless door
    dx = door["x"].to_f * MM_TO_IN; dy = door["y"].to_f * MM_TO_IN
    dw = (door["w"] || 900).to_f * MM_TO_IN
    dh = (door["h"] || 2000).to_f * MM_TO_IN
    wall = door["wall"] || "south"
    horiz = adir[1].abs < 1e-6
    vert  = adir[0].abs < 1e-6
    on = ((wall == "south" || wall == "north") && horiz && (dy - p1[1]).abs < 2.0) ||
         ((wall == "east"  || wall == "west")  && vert  && (dx - p1[0]).abs < 2.0)
    return nil unless on
    u = (dx - p1[0]) * adir[0] + (dy - p1[1]) * adir[1]
    u0 = [[u, u + dw].min, 0.0].max
    u1 = [[u, u + dw].max, len].min
    return nil if (u1 - u0) <= 0.01
    [u0, u1, dh]
  end

  # Build every wall of a polygon (outward normals from the winding), leaving a gap +
  # header where `door` lands on an edge.
  def self.poly_walls(ents, prefix, outline_in, thk, h, door, tag)
    ccw = signed_area(outline_in) > 0
    n = outline_in.length
    n.times do |i|
      p1 = outline_in[i]; p2 = outline_in[(i + 1) % n]
      dx = p2[0] - p1[0]; dy = p2[1] - p1[1]
      len = Math.sqrt(dx * dx + dy * dy)
      next if len < 1e-6
      adir = [dx / len, dy / len]
      outward = ccw ? [adir[1], -adir[0]] : [-adir[1], adir[0]]
      gap = door_on_edge(door, p1, adir, len)
      if gap
        u0, u1, dh = gap
        wall_seg(ents, "#{prefix}_#{i}a", p1, adir, 0.0, u0, outward, thk, h, 0.0, tag)
        wall_seg(ents, "#{prefix}_#{i}b", p1, adir, u1, len, outward, thk, h, 0.0, tag)
        wall_seg(ents, "#{prefix}_#{i}hdr", p1, adir, u0, u1, outward, thk, h - dh, dh, tag)
      else
        wall_seg(ents, "#{prefix}_#{i}", p1, adir, 0.0, len, outward, thk, h, 0.0, tag)
      end
    end
  end

  # v0.2: build an L-shaped metric suite (polygon shell + ensuite + built-ins). All spec
  # coordinates are millimetres; everything is converted to inches (SketchUp's unit).
  def self.build_suite(spec)
    model = Sketchup.active_model
    model.start_operation("InteriorAI suite build", true)
    ents = model.active_entities
    begin
      r = spec["room"]
      outline = r["outline_mm"].map { |p| [p[0].to_f * MM_TO_IN, p[1].to_f * MM_TO_IN] }
      raise "outline needs >=3 points" if outline.length < 3
      h   = (r["ceiling_mm"] || 2800).to_f * MM_TO_IN
      thk = (r["wall_thk_mm"] || 100).to_f * MM_TO_IN
      fth = 4.0   # floor slab (inches)

      shell = model.layers.add("SHELL")
      built = model.layers.add("BUILTIN")
      furn  = model.layers.add("FURNITURE")
      fixt  = model.layers.add("FIXTURE")

      poly_floor(ents, "floor", outline, fth, shell)
      poly_walls(ents, "wall", outline, thk, h, spec["door"], shell)

      # sub-rooms (ensuite): own walls (own ceiling height) + fixtures
      (spec["subrooms"] || []).each_with_index do |sr, si|
        so = sr["outline_mm"].map { |p| [p[0].to_f * MM_TO_IN, p[1].to_f * MM_TO_IN] }
        next if so.length < 3
        sh = (sr["ceiling_mm"] || 2000).to_f * MM_TO_IN
        poly_walls(ents, "sub#{si}", so, thk, sh, sr["door"], shell)
        (sr["fixtures"] || []).each do |fx|
          box(ents, "fixture: #{fx['name']}", fx["x"].to_f * MM_TO_IN, fx["y"].to_f * MM_TO_IN, 0,
              fx["w"].to_f * MM_TO_IN, fx["d"].to_f * MM_TO_IN, (fx["h"] || 400).to_f * MM_TO_IN, fixt)
        end
      end

      # built-in millwork (the studio core product) — accurate boxes at full/parametric height
      (spec["builtins"] || []).each do |b|
        bh = b["h"] ? b["h"].to_f * MM_TO_IN : h
        box(ents, "builtin: #{b['name']}", b["x"].to_f * MM_TO_IN, b["y"].to_f * MM_TO_IN, 0,
            b["w"].to_f * MM_TO_IN, b["d"].to_f * MM_TO_IN, bh, built)
      end

      # loose furniture — box primitives (the blockout; the friend swaps her components).
      (spec["items"] || []).each do |it|
        next if it["kind"] == "rug"
        box(ents, "item: #{it['name']}", it["x"].to_f * MM_TO_IN, it["y"].to_f * MM_TO_IN, 0,
            it["w"].to_f * MM_TO_IN, it["d"].to_f * MM_TO_IN, [(it["h"] || 400).to_f * MM_TO_IN, 0.5].max, furn)
      end

      # native overall dimensions (bounding box, in inches)
      xs = outline.map { |p| p[0] }; ys = outline.map { |p| p[1] }
      x0 = xs.min; x1 = xs.max; y0 = ys.min; y1 = ys.max
      dims_tag = model.layers.add("DIMENSIONS")
      d1 = ents.add_dimension_linear([x0, y0, 0], [x1, y0, 0], [0, -12, 0]); d1.layer = dims_tag
      d2 = ents.add_dimension_linear([x0, y0, 0], [x0, y1, 0], [-12, 0, 0]); d2.layer = dims_tag

      model.commit_operation
      model.active_view.zoom_extents if model.active_view

      begin
        view = model.active_view
        w = x1 - x0; d = y1 - y0
        eye = Geom::Point3d.new(x0 + w * 1.4, y0 - d * 0.4, h * 1.4)
        tgt = Geom::Point3d.new(x0 + w * 0.4, y0 + d * 0.5, h * 0.2)
        view.camera = Sketchup::Camera.new(eye, tgt, Z_AXIS, true, 45)
        model.pages.add("ISO")
      rescue => e
        puts "InteriorAI: scene/camera skipped (#{e.message})"
      end

      puts "InteriorAI: built SUITE #{((x1-x0)/MM_TO_IN).round}x#{((y1-y0)/MM_TO_IN).round}mm shell + " \
           "#{(spec['subrooms']||[]).length} sub-room(s) + #{(spec['builtins']||[]).length} built-ins + " \
           "#{(spec['items']||[]).length} items (NATIVE, editable)"
    rescue => e
      model.abort_operation
      puts "InteriorAI SUITE ERROR: #{e.message}"
      raise
    end
  end

  def self.build_rect(spec)
    model = Sketchup.active_model
    model.start_operation("InteriorAI build", true)   # single undoable op
    ents  = model.active_entities

    r   = spec["room"]
    w   = r["width_in"].to_f
    d   = r["depth_in"].to_f
    h   = r["ceiling_in"].to_f
    thk = (r["wall_thk_in"]  || 4.5).to_f
    fth = (r["floor_thk_in"] || 4.0).to_f
    door = r["door"] || { "w_in" => 32, "h_in" => 80 }
    dw   = (door["w_in"] || 32).to_f
    dh   = (door["h_in"] || 80).to_f

    raise "InteriorAI: bad room dims (w=#{w} d=#{d} h=#{h})" if w <= 0 || d <= 0 || h <= 0
    # Clamp the door inside the wall: a too-wide door inverts the piers, a too-tall
    # door makes a negative-height header that hangs into the opening. Neither
    # raises in SketchUp -> a silently-wrong model. Clamp instead.
    dw = [[dw, 1.0].max, w - 2 * thk].min
    dh = [[dh, 1.0].max, h].min

    shell = model.layers.add("SHELL")
    furn  = model.layers.add("FURNITURE")

    # Shell.
    box(ents, "floor",      0,    0, -fth, w,           d,   fth, shell)
    box(ents, "wall_north", -thk, d,  0,   w + 2 * thk, thk, h,   shell)
    box(ents, "wall_west",  -thk, 0,  0,   thk,         d,   h,   shell)
    box(ents, "wall_east",  w,    0,  0,   thk,         d,   h,   shell)
    # South wall WITH a centered door opening (piers + header, no boolean).
    door_l = (w - dw) / 2.0
    door_r = (w + dw) / 2.0
    box(ents, "wall_south_pier_L", -thk,   -thk, 0,  door_l + thk,       thk, h, shell)
    box(ents, "wall_south_pier_R", door_r, -thk, 0,  (w + thk) - door_r, thk, h, shell)
    header_h = h - dh
    box(ents, "wall_south_header", door_l, -thk, dh, dw, thk, header_h, shell) if header_h > 1e-6

    # Furniture: place the friend's real SketchUp components from the catalog when
    # available (turns the blockout into a render-ready, editable scene); fall back
    # to a primitive box for any kind without a mapped component.
    catalog = load_catalog
    (spec["items"] || []).each do |it|
      ht = [(it["h"] || 18).to_f, 0.5].max
      unless place_component(ents, catalog, it, furn)
        box(ents, "item: #{it['name']}", it["x"].to_f, it["y"].to_f, 0,
            it["w"].to_f, it["d"].to_f, ht, furn)
      end
    end

    # Native in-model DIMENSIONS (overall W x D). add_dimension_linear is a real
    # model-side entity since SketchUp 2014 (research-confirmed) -> the deliverable
    # ships self-dimensioned, which is the differentiator. offset_vector pushes the
    # dimension line outside the room.
    dims_tag = model.layers.add("DIMENSIONS")
    dw_dim = ents.add_dimension_linear([0, 0, 0], [w, 0, 0], [0, -12, 0]); dw_dim.layer = dims_tag
    dd_dim = ents.add_dimension_linear([0, 0, 0], [0, d, 0], [-12, 0, 0]); dd_dim.layer = dims_tag

    model.commit_operation
    model.active_view.zoom_extents if model.active_view

    # Preset ISO scene + camera so the deliverable opens on a good view (set the
    # view camera first, THEN capture it into a Page -- the version-safe pattern).
    begin
      view = model.active_view
      eye = Geom::Point3d.new(w * 1.4, -d * 0.4, h * 1.3)
      tgt = Geom::Point3d.new(w * 0.4, d * 0.5, h * 0.2)
      view.camera = Sketchup::Camera.new(eye, tgt, Z_AXIS, true, 45)
      model.pages.add("ISO")
    rescue => e
      puts "InteriorAI: scene/camera skipped (#{e.message})"
    end

    puts "InteriorAI: built #{r['type']} #{w.to_i}x#{d.to_i}in + #{(spec['items'] || []).length} items (NATIVE, editable)"
  rescue => e
    model.abort_operation if defined?(model) && model
    puts "InteriorAI ERROR: #{e.message}"
    raise
  end
end

InteriorAI.build
