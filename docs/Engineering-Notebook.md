# Engineering Journal — Team KERNEL
**WRO Future Engineers 2026 | Arecibo, Puerto Rico**

---

## January 20, 2026 — First Meeting

Today was our first official meeting as a team. The WRO Future Engineers challenge was launched on January 16th by TechnoInventor, so we spent the first few days reading through the rules and figuring out what we were actually getting ourselves into.

We have four people: Nayán, Yatziel, Yanrick, and Jesús. Our coach is Carlos Olivera. We split responsibilities based on what each of us is best at — Nayán is handling all the software and programming, Yatziel is on mechanical design, Jesús is taking care of electronics and sensors, and Yanrick is handling media and documentation.

We looked at the challenge requirements for Round 1 and Round 2 and started thinking about what hardware we'd need. We already had access to a LEGO SPIKE Prime set, so we decided to start there and see how far we could get.

Main goal from day one: keep it simple. We've seen teams over-engineer their robots and then spend competition day fixing things. We don't want that.

---

## Late January 2026 — Robot V1: LEGO Only

Our first version of the robot used only LEGO SPIKE Prime components:

- SPIKE Prime Hub (main controller)
- Large Motor (traction)
- Medium Motor (steering)
- Color Sensor (floor line detection)
- Official SPIKE Prime rechargeable battery (plugs directly into the hub)

The idea was to keep everything in one place. It drove, it could follow commands, and the color sensor could detect lines when it was close enough to the floor.

But "close enough" was the problem. The SPIKE Prime Color Sensor needs to be very close to the surface to read reliably — so close that by the time it detected a line, the robot was basically already past it. Response time was too slow for the speed we needed. And without a camera, we had no way to detect obstacles or plan any kind of path.

We knew going into the first regional that V1 had real limitations. We went anyway to learn.

---

## February 21, 2026 — First Regional Competition

We competed in the first regional with V1.

It was a tough day. The color sensor range issues we'd seen in practice were even more obvious on the actual competition track. We couldn't get consistent lap completions. The robot was functional but not competition-ready at the level we needed.

The experience was still worth it. We saw the real track setup and lighting conditions, and it completely confirmed what we already suspected: LEGO sensors alone were not going to work for this challenge. The sensor range just isn't there.

After the regional, we made the call — we were rebuilding.

---

## Late February 2026 — The Decision: Robot V2

After the first regional, we defined what V2 would look like. The goal was to keep what worked from V1 and replace everything that didn't.

**What we kept:**
- LEGO Large Motor (traction) — precise, reliable, no reason to replace it
- LEGO Medium Motor (steering) — same
- LEGO wheels — still using these for now

**What we added:**
- Raspberry Pi 4B as the main controller
- LEGO SPIKE Prime Build HAT to connect the Pi to the LEGO motors
- Arducam IMX708 12MP camera — this becomes the main sensor for everything
- 3× VL53L0X ToF distance sensors (acquired and tested, not used in competition yet)
- BNO08X IMU (acquired and tested, not used in competition yet)
- TCA9548A I2C multiplexer for the sensors
- LX-2BUPS boost module + 2× 18650 Li-ion batteries

**The power problem** hit us right away. V1 ran off the official SPIKE Prime hub battery. Simply plug it in, and it works. V2 is completely different. The Raspberry Pi and Build HAT need an external power source, and the Build HAT specifically requires 8–12V through a barrel jack.

Finding the right battery setup took significant time and research. This was one of the main reasons we couldn't participate in the second regional on March 28th — we hadn't fully validated the power system in time. We also designed and printed a custom case to hold the LX-2BUPS module and the 18650 cells securely on the chassis.

---

## March 28, 2026 — Second Regional (We Couldn't Participate)

The second regional was on March 28th. Between the power system not being fully validated and the overall state of V2, we made the decision not to compete. We used the time to keep building and get the system solid.

---

## Early March 2026 — Building V2: First Problems

We started assembling V2. The first big problem: the motors didn't respond at all.

The Build HAT library wasn't throwing errors; it just wasn't communicating. After a lot of searching, we found the issue: a line in the Raspberry Pi boot file (`cmdline.txt`) called `console=serial0,115200` makes the OS claim the serial port before the Build HAT can use it. Delete it, add `dtoverlay=disable-bt` and `enable_uart=1` to the other config file — and it works.

No error message, no warning. Just silence. Finding this took way longer than it should have.

---

## Mid March 2026 — Camera Setup

We connected the Arducam IMX708 via CSI ribbon cable. First attempt: nothing.

The ribbon cable was inserted backwards. The IMX708 cable has a specific orientation; flip it, and the camera doesn't initialize with no error explaining why. Physical check fixed it.

After adding `dtoverlay=imx708` to the config file, the camera worked. We set up `wro_camera.py` — a Flask server that processes frames and detects colors using HSV. It streams live to any browser on the network at port 5000, and shows detections with position (left, center, right) and distance (far, medium, close, very close) in real time.

---

## Late March / Early April 2026 — Color Detection and Testing

We built `calibrar_colores.py` — interactive HSV sliders to tune color ranges in real time.

We also used the official color values in the WRO 2026 rulebook (pages 26–28):

| Element | Official Color | Notes |
|---------|---------------|-------|
| Orange line | CMYK(0, 60, 100, 0) | ~RGB(255, 102, 0) |
| Blue line | CMYK(100, 80, 0, 0) | ~RGB(0, 51, 255) |
| Red obstacle | RGB(238, 39, 55) | |
| Green obstacle | RGB(68, 214, 44) | |
| Magenta parking | RGB(255, 0, 255) | Pure magenta |

Having the exact official colors made calibration much more accurate than guessing.

**Zone filter:** We restricted orange and blue line detection to only the bottom half of the camera frame. The cardboard walls on the practice track are also detected as orange and red without this filter; the robot turned randomly whenever it saw a wall. One of the most important fixes in the whole project.

**Silent bug we hit:** The vision server sent data as `"linea_naranja"`, but the robot code looked for `"naranja"`. Wrong key name, complete failure, no error messages. We now double-check every key name any time detection stops working.

**Double-counting fix:** Without a 3-second blocking window after each turn, the robot detected the same corner line twice and counted it twice. We spent a while figuring out why it was finishing "6 laps" when it had only done 3.

---

## Mid March 2026 — Sensor Testing (ToF and IMU)

Even though we're not using the ToF sensors or IMU in competition yet, we tested them to confirm they work and understand how to integrate them later.

We set up the TCA9548A multiplexer on a breadboard with the BNO08X IMU and connected it to the Raspberry Pi. Using `i2cdetect -y 1`, we confirmed both devices were visible on the I2C bus — the multiplexer at address `0x70` and the IMU at `0x4b`.

We then ran `test_imu.py` and got quaternion data streaming in real time — the IMU initialized correctly and was reading orientation continuously.

The ToF sensors and IMU are ready to be integrated into the main program in a future version. For this regional we're keeping things simple and running on camera only.

---

## April 2026 — Competition Strategy Decision

**Camera-only approach for the third regional.**

After evaluating the time we have left before the April 19th competition and the current state of the robot, we made a deliberate decision: run this regional using only the camera, without the ToF sensors or IMU.

The reasons:

1. The camera already detects everything we need — line colors, obstacle colors, positions, and distances
2. Fewer components = fewer things that can fail on competition day
3. The ToF and IMU work but haven't been integrated and tested in the full robot loop yet
4. Two days is not enough time to safely integrate, test, and validate new sensors before a competition

The camera gives us:
- Orange/blue line detection → turn direction for Round 1
- Red/green obstacle detection → bypass direction for Round 2
- Position (left, center, right) → where the obstacle is
- Distance (far, medium, close, very close) → when to start the maneuver

That's everything we need to run both rounds.

**Single program for both rounds.**

We also decided to keep everything in one program — `kernel_robot_r1.py` — rather than splitting Round 1 and Round 2 into separate files. The same program handles both: it completes 3 laps reading orange/blue lines, and during those laps, it also reacts to red and green obstacles. One program, less complexity, easier to debug on competition day.

The obstacle avoidance logic:
```
If camera sees red obstacle → steer right to bypass
If camera sees green obstacle → steer left to bypass
Trigger when distance = "close" or "very close"
After bypass → return to center and continue
```

---

## Current State — Before April 19 Regional

**Working:**
- Orange/blue line detection and automatic turn direction ✅
- Post-turn blocking window (3 seconds) ✅
- Corner and lap counting (12 corners = 3 laps) ✅
- Camera autostart on boot via systemd ✅
- Access via ethernet/laptop ✅
- Power system with 18650 cells + LX-2BUPS ✅
- Custom battery/UPS case designed and printed ✅
- Red/green obstacle detection with position and distance ✅

**In progress before Saturday:**
- Obstacle avoidance maneuver logic (steering around obstacles)
- Full Round 1 + Round 2 combined test run
- HSV calibration with official competition colors
- Battery endurance validation

**Planned for future versions:**
- Integrate ToF sensors for more precise distance measurement
- Integrate IMU for heading correction
- Separate Round 1 and Round 2 into cleaner code modules
- Custom 3D-printed wheels (designing in progress)

---

## Reflections So Far

The biggest lesson from this project isn't technical. It's that you have to be willing to start over when something isn't working. We built a full robot, competed with it, and rebuilt it from scratch because we knew it wasn't going to get us where we needed to be.

The power system challenge was one of the hardest non-code problems we faced. Going from a plug-in LEGO battery to a custom setup with boost modules and 18650 cells is a big jump — it slowed us down and cost us the second regional. But now we understand every part of our power system, and we have built a case for it.

The camera-only decision for this regional is also an engineering choice we're proud of. It would be easy to throw every sensor at the problem and hope it works. Instead, we asked: what do we actually need to complete the challenge? And the answer was simpler than we expected.

---

*Journal maintained by Team KERNEL — Barceloneta, Puerto Rico 🇵🇷*

