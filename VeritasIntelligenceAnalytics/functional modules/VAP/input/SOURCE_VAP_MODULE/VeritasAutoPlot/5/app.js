/* ============================================
   SPACE RACE TIMELINE — app.js
   Interactive horizontal-scrolling timeline
   ============================================ */

(function () {
  'use strict';

  // ============================================
  // EMBEDDED DATA
  // ============================================

  const EVENTS = [
    {"date":"1957-08-21","year":1957,"mission":"R-7 ICBM / Semyorka","country":"USSR","category":"milestone","description":"The R-7 (Semyorka), designed by Korolev, was the world's first intercontinental ballistic missile and became the launch vehicle that orbited Sputnik, Vostok, and the early Luna probes. Its surplus thrust over what was needed for a nuclear warhead made it ideal for launching satellites.","success":true},
    {"date":"1957-10-04","year":1957,"mission":"Sputnik 1","country":"USSR","category":"milestone","description":"First artificial satellite in history, launched on a modified R-7 ICBM. Orbited Earth every 96 minutes, transmitting radio beeps for 22 days until its batteries died on October 26; it remained in orbit until burning up on January 4, 1958.","success":true},
    {"date":"1957-11-03","year":1957,"mission":"Sputnik 2","country":"USSR","category":"milestone","description":"Carried Laika the dog, the first living creature in Earth orbit. There was never a plan to return her alive; she died within hours from overheating when the thermal control system failed, but the mission proved a living organism could survive a rocket launch.","success":true},
    {"date":"1957-12-06","year":1957,"mission":"Vanguard TV3","country":"US","category":"failure","description":"America's first attempt to launch a satellite ended in a nationally televised disaster when the Vanguard rocket lost thrust two seconds after liftoff, rose just four feet, fell back, and exploded on the pad. The press dubbed it 'Kaputnik' and 'Flopnik.'","success":false},
    {"date":"1958-01-31","year":1958,"mission":"Explorer 1","country":"US","category":"milestone","description":"The first successful US satellite, launched by a Jupiter-C rocket built in 84 days by Wernher von Braun's team. Its Geiger counter detected the Van Allen radiation belts surrounding Earth, a major scientific discovery.","success":true},
    {"date":"1958-03-17","year":1958,"mission":"Vanguard 1","country":"US","category":"milestone","description":"The first solar-powered satellite, and the oldest human-made object still in orbit. Its precise tracking revealed that Earth is slightly pear-shaped, refining knowledge of the planet's gravitational field.","success":true},
    {"date":"1958-10-01","year":1958,"mission":"NASA Founded","country":"US","category":"milestone","description":"NASA officially began operations on October 1, 1958, absorbing the National Advisory Committee for Aeronautics (NACA) and taking over civilian space activities. Created in direct response to Sputnik's shock, it unified fragmented American space efforts.","success":true},
    {"date":"1959-01-02","year":1959,"mission":"Luna 1","country":"USSR","category":"robotic","description":"Intended to impact the Moon but missed by about 6,000 km due to a timing error, becoming instead the first spacecraft to escape Earth's gravity and enter heliocentric orbit. It was the first man-made object to reach the vicinity of the Moon.","success":true},
    {"date":"1959-09-12","year":1959,"mission":"Luna 2","country":"USSR","category":"robotic","description":"The first spacecraft to reach another celestial body, impacting the Moon on September 13 in the Palus Putredinis region. It confirmed the Moon has no significant magnetic field and no radiation belts.","success":true},
    {"date":"1959-10-04","year":1959,"mission":"Luna 3","country":"USSR","category":"robotic","description":"Flew around the Moon and photographed its far side for the first time in history, revealing a surface markedly different from the near side, with fewer maria. The images transformed lunar science and geography.","success":true},
    {"date":"1961-04-12","year":1961,"mission":"Vostok 1","country":"USSR","category":"crewed","description":"Yuri Gagarin became the first human to travel into space, completing one orbit of Earth in 108 minutes and landing safely by ejecting from the capsule and parachuting separately. His call sign was 'Kedr'; his exclamation at launch\u2014'Poyekhali!' (Let's go!)\u2014became iconic.","success":true},
    {"date":"1961-05-05","year":1961,"mission":"Mercury-Redstone 3 (Freedom 7)","country":"US","category":"crewed","description":"Alan Shepard became the first American in space on a 15-minute 28-second suborbital flight, reaching an altitude of 187 km. Though far shorter than Gagarin's orbital mission, it restored American confidence.","success":true},
    {"date":"1961-05-25","year":1961,"mission":"Kennedy Moon Challenge","country":"US","category":"milestone","description":"President John F. Kennedy declared before Congress: 'This nation should commit itself to achieving the goal, before this decade is out, of landing a man on the Moon and returning him safely to the Earth.' The speech defined American space policy for the decade.","success":true},
    {"date":"1961-08-06","year":1961,"mission":"Vostok 2","country":"USSR","category":"crewed","description":"Gherman Titov completed 17 orbits over 25 hours\u2014the first person to spend more than a day in space. He was the youngest person ever to fly in space (25 years old) and the first to sleep in orbit, though he experienced space sickness.","success":true},
    {"date":"1962-02-20","year":1962,"mission":"Mercury-Atlas 6 (Friendship 7)","country":"US","category":"crewed","description":"John Glenn became the first American to orbit Earth, completing three orbits in 4 hours and 55 minutes. A faulty sensor warning about the heat shield kept ground controllers in suspense during reentry.","success":true},
    {"date":"1962-04-23","year":1962,"mission":"Ranger 4","country":"US","category":"robotic","description":"Impacted the far side of the Moon\u2014technically the first US object to reach the Moon\u2014but a computer timer failure disabled all scientific instruments before launch, returning no data.","success":false},
    {"date":"1962-08-27","year":1962,"mission":"Mariner 2","country":"US","category":"robotic","description":"The first successful planetary probe, Mariner 2 flew past Venus on December 14, 1962 at 34,773 km. It confirmed Venus has extremely high surface temperatures (~425\u00b0C).","success":true},
    {"date":"1962-10-03","year":1962,"mission":"Mercury-Atlas 8 (Sigma 7)","country":"US","category":"crewed","description":"Wally Schirra completed six orbits in 9 hours and 13 minutes, operating the spacecraft with exemplary fuel efficiency and earning the mission the nickname 'textbook flight.'","success":true},
    {"date":"1963-05-15","year":1963,"mission":"Mercury-Atlas 9 (Faith 7)","country":"US","category":"crewed","description":"Final Mercury mission; Gordon Cooper completed 22 orbits in 34 hours. Cooper manually controlled reentry after an electrical failure, achieving greater precision than the automated system.","success":true},
    {"date":"1963-06-16","year":1963,"mission":"Vostok 6","country":"USSR","category":"crewed","description":"Valentina Tereshkova became the first woman in space, orbiting Earth 48 times over nearly three days on a solo mission. She remains the only woman to have flown a solo space mission.","success":true},
    {"date":"1964-01-30","year":1964,"mission":"Ranger 6","country":"US","category":"robotic","description":"Navigated flawlessly to impact the Moon but TV cameras failed to operate due to accidental activation during launch that burned out the imaging system. Returned zero photographs.","success":false},
    {"date":"1964-10-12","year":1964,"mission":"Voskhod 1","country":"USSR","category":"crewed","description":"First spacecraft to carry multiple crew members\u2014commander Vladimir Komarov, engineer Konstantin Feoktistov, and physician Boris Yegorov. The crew famously flew without pressure suits.","success":true},
    {"date":"1964-11-28","year":1964,"mission":"Mariner 4","country":"US","category":"robotic","description":"First successful Mars flyby on July 14, 1965, returning 21 close-up images that revealed a cratered, dead-looking surface. The images largely ended speculation about Martian canals.","success":true},
    {"date":"1965-03-18","year":1965,"mission":"Voskhod 2","country":"USSR","category":"crewed","description":"Alexei Leonov performed the world's first spacewalk (EVA), spending 12 minutes outside the spacecraft. His spacesuit dangerously over-inflated in vacuum, forcing him to bleed air to re-enter the airlock.","success":true},
    {"date":"1965-03-23","year":1965,"mission":"Gemini 3","country":"US","category":"crewed","description":"First crewed Gemini flight with Gus Grissom and John Young, completing three orbits and testing the spacecraft's maneuvering thrusters. Grissom smuggled a corned beef sandwich aboard.","success":true},
    {"date":"1965-06-03","year":1965,"mission":"Gemini IV","country":"US","category":"crewed","description":"Ed White became the first American to walk in space (EVA), spending 22 minutes outside the spacecraft and maneuvering with a handheld thruster gun. White had to be ordered back inside.","success":true},
    {"date":"1965-07-28","year":1965,"mission":"Ranger 7","country":"US","category":"robotic","description":"First successful US lunar mission after six straight failures, transmitting 4,316 high-resolution photos of the Moon before impact. Images 1,000 times sharper than any from Earth.","success":true},
    {"date":"1965-10-12","year":1965,"mission":"Luna 7","country":"USSR","category":"robotic","description":"Soviet attempt at a lunar soft landing that failed when retrorockets fired too early; the probe impacted the Moon in Oceanus Procellarum at high velocity.","success":false},
    {"date":"1965-12-04","year":1965,"mission":"Gemini VII","country":"US","category":"crewed","description":"Frank Borman and James Lovell spent 14 days in space, proving humans could endure a round-trip lunar mission. The spacecraft served as rendezvous target for Gemini VI-A.","success":true},
    {"date":"1965-12-15","year":1965,"mission":"Gemini VI-A","country":"US","category":"crewed","description":"Wally Schirra and Tom Stafford accomplished the first space rendezvous, maneuvering to within one foot of Gemini VII and station-keeping for over five hours.","success":true},
    {"date":"1966-01-14","year":1966,"mission":"Death of Sergei Korolev","country":"USSR","category":"milestone","description":"Sergei Korolev, the 'Chief Designer' who secretly drove the entire Soviet space program, died during routine surgery at age 59. The Soviet program fractured without his unifying authority.","success":false},
    {"date":"1966-01-31","year":1966,"mission":"Luna 9","country":"USSR","category":"robotic","description":"First spacecraft to achieve a soft landing on the Moon, touching down in Oceanus Procellarum. It returned panoramic photographs and proved the Moon was solid enough to support a spacecraft.","success":true},
    {"date":"1966-03-16","year":1966,"mission":"Gemini 8","country":"US","category":"crewed","description":"Neil Armstrong and David Scott achieved the first docking of two spacecraft in orbit. A stuck thruster sent the craft into a dangerous spin; Armstrong used reentry thrusters to regain control.","success":true},
    {"date":"1966-03-31","year":1966,"mission":"Luna 10","country":"USSR","category":"robotic","description":"First spacecraft to achieve orbit around the Moon, studying the lunar gravitational field, magnetic field, and cosmic radiation. Broadcast the Internationale during the 23rd Communist Party Congress.","success":true},
    {"date":"1966-05-30","year":1966,"mission":"Surveyor 1","country":"US","category":"robotic","description":"First US spacecraft to soft-land on the Moon. Transmitted over 11,000 images and confirmed the surface was strong enough to support the weight of an Apollo lunar module.","success":true},
    {"date":"1966-09-12","year":1966,"mission":"Gemini XI","country":"US","category":"crewed","description":"Charles Conrad and Richard Gordon boosted to a record altitude of 1,369 km using an Agena target vehicle engine. Demonstrated performance needed for lunar orbital operations.","success":true},
    {"date":"1966-11-11","year":1966,"mission":"Gemini XII","country":"US","category":"crewed","description":"Final Gemini mission; Buzz Aldrin set an EVA record of 5.5 hours total. The Gemini program's 10 crewed missions in 20 months mastered all skills needed for Apollo.","success":true},
    {"date":"1967-01-27","year":1967,"mission":"Apollo 1","country":"US","category":"failure","description":"A cabin fire during a ground test killed Gus Grissom, Ed White, and Roger Chaffee in seconds. The pure oxygen atmosphere and flammable materials caused rapid incineration; the tragedy forced an 18-month redesign.","success":false},
    {"date":"1967-04-23","year":1967,"mission":"Soyuz 1","country":"USSR","category":"failure","description":"Vladimir Komarov became the first human to die in spaceflight when the parachute system failed on reentry, crashing at terminal velocity. The mission flew despite engineers' documented warnings.","success":false},
    {"date":"1967-11-09","year":1967,"mission":"Apollo 4 (Saturn V first flight)","country":"US","category":"milestone","description":"First uncrewed test flight of the Saturn V, the most powerful rocket ever flown. Its five F-1 engines generated 7.5 million pounds of thrust and performed flawlessly.","success":true},
    {"date":"1968-09-14","year":1968,"mission":"Zond 5","country":"USSR","category":"robotic","description":"First spacecraft to fly around the Moon and return to Earth, carrying tortoises, fruit flies, plants, and bacteria. Suggested the Soviets were preparing for a crewed lunar flyby.","success":true},
    {"date":"1968-10-11","year":1968,"mission":"Apollo 7","country":"US","category":"crewed","description":"First crewed Apollo mission, spending 11 days in Earth orbit testing the redesigned command module. Featured the first live TV broadcast from an American crewed spacecraft.","success":true},
    {"date":"1968-11-10","year":1968,"mission":"Zond 6","country":"USSR","category":"robotic","description":"Soviet circumlunar probe that flew around the Moon. A cabin seal failure depressurized the payload; the capsule was destroyed during landing when the parachute cut loose prematurely.","success":false},
    {"date":"1968-12-21","year":1968,"mission":"Apollo 8","country":"US","category":"crewed","description":"First crewed spacecraft to leave Earth orbit. Frank Borman, Jim Lovell, and Bill Anders flew to the Moon and completed 10 lunar orbits on Christmas Eve. They photographed the iconic 'Earthrise' image.","success":true},
    {"date":"1969-02-21","year":1969,"mission":"N1 Rocket - First Test (3L)","country":"USSR","category":"failure","description":"First launch attempt of the Soviet Moon rocket N1. First-stage engines began failing seconds after liftoff; the vehicle crashed 183 seconds into flight.","success":false},
    {"date":"1969-03-03","year":1969,"mission":"Apollo 9","country":"US","category":"crewed","description":"First crewed test of the Lunar Module in Earth orbit. The crew performed the first transfer through a tunnel between docked spacecraft, validating all Apollo components.","success":true},
    {"date":"1969-05-18","year":1969,"mission":"Apollo 10","country":"US","category":"crewed","description":"Full dress rehearsal for the Moon landing. Tom Stafford, John Young, and Gene Cernan descended to within 15.6 km of the surface in the Lunar Module.","success":true},
    {"date":"1969-07-03","year":1969,"mission":"N1 Rocket - Second Test (5L)","country":"USSR","category":"failure","description":"The N1's second launch ended in one of the largest non-nuclear explosions in history when the vehicle crashed back onto its launch pad 10 seconds after liftoff, destroying Launch Pad 110 East.","success":false},
    {"date":"1969-07-13","year":1969,"mission":"Luna 15","country":"USSR","category":"robotic","description":"Soviet attempt to return a robotic lunar sample before Apollo 11. Luna 15 was orbiting the Moon while Apollo 11 astronauts were on the surface; it crashed hours before Armstrong and Aldrin departed.","success":false},
    {"date":"1969-07-16","year":1969,"mission":"Apollo 11","country":"US","category":"crewed","description":"Neil Armstrong and Buzz Aldrin landed in the Sea of Tranquility on July 20, making Armstrong the first human to walk on the Moon. 'One small step for [a] man, one giant leap for mankind.'","success":true},
    {"date":"1969-11-14","year":1969,"mission":"Apollo 12","country":"US","category":"crewed","description":"Pete Conrad and Alan Bean landed in the Ocean of Storms with pinpoint precision, walking to the Surveyor 3 probe. The crew was struck by lightning twice during launch.","success":true},
    {"date":"1970-04-11","year":1970,"mission":"Apollo 13","country":"US","category":"crewed","description":"An oxygen tank explosion forced Jim Lovell, Jack Swigert, and Fred Haise to abort the Moon landing and shelter in the Lunar Module as a lifeboat. All three returned safely.","success":false},
    {"date":"1970-09-12","year":1970,"mission":"Luna 16","country":"USSR","category":"robotic","description":"First robotic mission to land on the Moon and return soil samples to Earth, collecting 101 grams of basalt from Mare Fecunditatis. Fully automatic from landing through re-entry.","success":true},
    {"date":"1970-11-10","year":1970,"mission":"Luna 17 / Lunokhod 1","country":"USSR","category":"robotic","description":"Delivered the first robotic lunar rover, Lunokhod 1. The solar-powered rover operated for 322 days, traveling 10.5 km and transmitting over 20,000 photos.","success":true},
    {"date":"1971-01-31","year":1971,"mission":"Apollo 14","country":"US","category":"crewed","description":"Alan Shepard and Edgar Mitchell landed at Fra Mauro. Shepard famously hit two golf balls with a makeshift club; both conducted detailed geological fieldwork.","success":true},
    {"date":"1971-04-19","year":1971,"mission":"Salyut 1","country":"USSR","category":"milestone","description":"First space station ever placed in orbit. The first docking crew couldn't enter due to a hatch fault; the second crew spent 23 days aboard but all three cosmonauts died during reentry.","success":true},
    {"date":"1971-06-06","year":1971,"mission":"Soyuz 11 / Salyut 1","country":"USSR","category":"crewed","description":"Georgy Dobrovolsky, Viktor Patsayev, and Vladislav Volkov spent a record 23 days aboard Salyut 1. All three died when a valve opened accidentally during reentry.","success":false},
    {"date":"1971-06-26","year":1971,"mission":"N1 Rocket - Third Test (6L)","country":"USSR","category":"failure","description":"The N1's third launch attempt failed when an uncontrolled roll developed immediately after liftoff that the control system could not correct.","success":false},
    {"date":"1971-07-26","year":1971,"mission":"Apollo 15","country":"US","category":"crewed","description":"David Scott and Jim Irwin used the first Lunar Roving Vehicle in the Hadley-Apennine highlands. The mission collected 77 kg of samples including the 'Genesis Rock.'","success":true},
    {"date":"1972-04-16","year":1972,"mission":"Apollo 16","country":"US","category":"crewed","description":"John Young and Charles Duke explored the Descartes Highlands, the first mission to the lunar highlands. Young drove the rover 27 km in three EVAs.","success":true},
    {"date":"1972-11-23","year":1972,"mission":"N1 Rocket - Fourth Test (7L)","country":"USSR","category":"failure","description":"The N1's fourth and final launch attempt flew 107 seconds before a central engine cluster failed. The N1 program was quietly cancelled by 1974.","success":false},
    {"date":"1972-12-07","year":1972,"mission":"Apollo 17","country":"US","category":"crewed","description":"The final Apollo Moon mission. Geologist Harrison Schmitt was the first scientist on the Moon. Gene Cernan said 'we leave as we came.' No humans have returned since.","success":true},
    {"date":"1973-05-14","year":1973,"mission":"Skylab","country":"US","category":"milestone","description":"America's first space station, launched on a Saturn V. Severely damaged when a micrometeorite shield tore away; a repair crew improvised a sunshade 11 days later.","success":true},
    {"date":"1973-05-25","year":1973,"mission":"Skylab 2","country":"US","category":"crewed","description":"Pete Conrad, Paul Weitz, and Joseph Kerwin spent 28 days repairing Skylab and conducting experiments. They performed a spacewalk to free the jammed solar panel.","success":true},
    {"date":"1973-07-28","year":1973,"mission":"Skylab 3","country":"US","category":"crewed","description":"Alan Bean, Jack Lousma, and Owen Garriott spent 59 days aboard Skylab, completing 150% of mission objectives. Nearly ended early when three of four gyros failed.","success":true},
    {"date":"1973-11-16","year":1973,"mission":"Skylab 4","country":"US","category":"crewed","description":"Gerald Carr, Edward Gibson, and William Pogue spent a record 84 days in space. The crew famously staged a 'workers' revolt,' taking an unscheduled day off.","success":true},
    {"date":"1974-06-02","year":1974,"mission":"Salyut 3","country":"USSR","category":"milestone","description":"A military reconnaissance space station equipped with a mounted cannon for self-defense\u2014the only armed spacecraft in history. Successfully occupied for 16 days.","success":true},
    {"date":"1974-12-26","year":1974,"mission":"Salyut 4","country":"USSR","category":"milestone","description":"A second-generation civilian space station with improved solar power. Successfully occupied by two crews conducting astrophysics and biomedical research.","success":true},
    {"date":"1975-07-15","year":1975,"mission":"Apollo-Soyuz Test Project","country":"US","category":"crewed","description":"The last Apollo mission and first US-Soviet joint spaceflight. Tom Stafford and Alexei Leonov shook hands in orbit in a historic gesture of Cold War d\u00e9tente.","success":true},
    {"date":"1975-07-15","year":1975,"mission":"Soyuz 19","country":"USSR","category":"crewed","description":"Soviet half of the Apollo-Soyuz Test Project. Alexei Leonov and Valery Kubasov docked with the Apollo capsule. The mission symbolically ended the Space Race.","success":true}
  ];

  const WHATIF = [
    {"proposed_year":1969,"country":"USSR","mission":"N1-L3 Crewed Lunar Landing","description":"A single Soviet cosmonaut would land on the Moon using the LK lunar lander, while a second cosmonaut waited in the LOK lunar orbiter.","what_if":"Had the N1 flown successfully, the USSR could have beaten or tied the United States to the Moon. A successful Soviet lunar landing would have radically changed the Cold War narrative.","cancelled_reason":"Four consecutive N1 launch failures between 1969 and 1972. Program cancelled in 1976.","category":"crewed"},
    {"proposed_year":1972,"country":"US","mission":"Apollo 18 \u2014 Schr\u00f6ter's Valley","description":"A J-class lunar surface mission to the Aristarchus Plateau, the most geologically diverse region on the Moon.","what_if":"Landing on the Aristarchus Plateau would have been the most geologically rich Apollo landing, possibly settling key debates about lunar volcanic chronology.","cancelled_reason":"Cancelled September 1970 due to Congressional budget cuts. All hardware had already been manufactured.","category":"crewed"},
    {"proposed_year":1973,"country":"US","mission":"Apollo 19 \u2014 Hyginus Rille","description":"A J-class mission targeting the Hyginus Rille region, a 220-km chain of craters possibly of volcanic origin.","what_if":"Would have clarified whether some lunar rilles are volcanic calderas or impact chains\u2014a question unresolved to this day.","cancelled_reason":"Cancelled September 1970, simultaneously with Apollo 18, due to Congressional budget cuts.","category":"crewed"},
    {"proposed_year":1974,"country":"US","mission":"Apollo 20 \u2014 Tycho Crater","description":"The last cancelled J-class mission. Tycho crater, 108 million years old, could have provided an absolute age anchor for lunar chronology.","what_if":"Tycho samples would have yielded the most precise absolute age of any Apollo site, potentially calibrating the entire impact flux model for the inner Solar System.","cancelled_reason":"Cancelled January 1970 so its Saturn V could launch Skylab.","category":"crewed"},
    {"proposed_year":1972,"country":"US","mission":"Manned Orbiting Laboratory (MOL)","description":"A top-secret USAF/NRO crewed military space station for reconnaissance from low polar orbit.","what_if":"MOL would have been the first continuously crewed US space station, predating Skylab by years, with real-time intelligence-gathering capability.","cancelled_reason":"Cancelled June 1969 by President Nixon. Automated satellites had advanced enough to make crewed advantage marginal.","category":"military"},
    {"proposed_year":1968,"country":"USSR","mission":"Almaz Military Space Station","description":"Vladimir Chelomei's military orbital station designed for reconnaissance, with TKS resupply vehicles.","what_if":"A fully operational Almaz/TKS system would have established a permanent Soviet military space presence a decade before Mir.","cancelled_reason":"Undermined by bureaucratic rivalry, funding diversions, and loss of political patron after Khrushchev's ouster.","category":"military"},
    {"proposed_year":1966,"country":"US","mission":"X-20 Dynasoar","description":"A USAF single-pilot reusable spaceplane for reconnaissance, orbital bombing, and satellite interception. Neil Armstrong was among the selected test pilots.","what_if":"The US would have possessed the world's first orbital spaceplane 15 years before the Space Shuttle, with anti-satellite capability.","cancelled_reason":"Cancelled December 1963 by McNamara. No clear weapons system mission in the foreseeable future.","category":"military"},
    {"proposed_year":1975,"country":"US","mission":"NERVA Nuclear Rocket","description":"A nuclear thermal rocket engine with twice the specific impulse of chemical rockets. Ground tests ran flawlessly; NASA planned a crewed Mars mission by 1978.","what_if":"With NERVA, a crewed Mars mission in the late 1970s was technically feasible. The journey time could be cut from ~9 months to ~4-5 months.","cancelled_reason":"Cancelled January 1973 by Nixon during post-Apollo budget cuts. No committed mission for the technology.","category":"propulsion"},
    {"proposed_year":1971,"country":"USSR","mission":"Soviet TMK Mars Expedition","description":"A three-cosmonaut Mars flyby mission launched on a single N1, reaching Mars after 10.5 months and returning after a 3-year journey.","what_if":"A crewed Mars flyby in 1971 would have electrified the world and given the USSR an extraordinary propaganda victory as Apollo wound down.","cancelled_reason":"Never officially approved. All variants depended on the N1, which never successfully flew.","category":"crewed"},
    {"proposed_year":1972,"country":"USSR","mission":"Soyuz Kontakt","description":"The Kontakt docking system for the Soviet crewed lunar landing program's lunar-orbit rendezvous phase, requiring EVA for crew transfer.","what_if":"A successful test might have sustained enough momentum for at least one crewed N1-L3 lunar attempt.","cancelled_reason":"Continuously postponed from 1970 and cancelled without flying after Apollo 11 reduced political incentive.","category":"crewed"},
    {"proposed_year":1966,"country":"USSR","mission":"Voskhod 3 \u2014 Long-Duration","description":"An 18-20 day endurance mission including the first tethered artificial gravity experiment.","what_if":"Would have given the USSR momentum heading into the Soyuz era rather than the long gap in Soviet crewed spaceflight that ended with fatal Soyuz 1.","cancelled_reason":"Never officially cancelled\u2014it 'faded away' after Korolev's death. Resources redirected to Soyuz.","category":"crewed"},
    {"proposed_year":1965,"country":"USSR","mission":"Spiral Aerospace System","description":"A Mikoyan reusable orbital spaceplane launched from a Mach 4-6 carrier aircraft, for military reconnaissance and satellite interception.","what_if":"The USSR would have fielded the world's first operational military spaceplane\u2014a capability the US did not match until the X-37B in 2010.","cancelled_reason":"Cancelled 1978 when the Soviet military pivoted to building Buran in response to the US Space Shuttle.","category":"military"},
    {"proposed_year":1975,"country":"USSR","mission":"Zvezda Lunar Base","description":"A permanent crewed lunar base with nine modules, nuclear reactors, and a 'lunar train' for 60-day surface traverses.","what_if":"A Soviet lunar base by the late 1970s would have been a geopolitical event of enormous magnitude\u2014effectively a permanent territorial claim on the Moon.","cancelled_reason":"Cancelled with the N1 program in 1974. Estimated cost of 50 billion rubles was prohibitive.","category":"infrastructure"},
    {"proposed_year":1977,"country":"USSR","mission":"Lunokhod 3","description":"The third and most capable Soviet lunar rover, fully flight-ready but never launched. Now displayed at the NPO Lavochkin museum.","what_if":"Design improvements could have enabled a multi-year mission, particularly at a polar region of enormous scientific value only appreciated decades later.","cancelled_reason":"Cancelled due to lack of launch vehicles after the N1 cancellation in 1974.","category":"robotic"},
    {"proposed_year":1959,"country":"US","mission":"Project Horizon \u2014 Lunar Outpost","description":"A 1959 US Army plan for a permanent military base on the Moon by 1966, staffed by 12 soldiers, armed and nuclear-powered.","what_if":"Would have placed US soldiers on the Moon in 1965\u2014four years before Apollo 11\u2014and made the Moon a Cold War battleground.","cancelled_reason":"Rejected by Eisenhower when space responsibility was transferred to civilian NASA. Cost was prohibitive.","category":"military"},
    {"proposed_year":1972,"country":"US","mission":"Apollo Applications Program","description":"NASA's plan for extended Apollo missions: a crewed Venus flyby, space stations, extended lunar stays, and a permanent lunar outpost.","what_if":"A crewed Venus flyby in 1973 would have been mankind's first visit to another planet, and the momentum could have supported a Mars mission by the early 1980s.","cancelled_reason":"Budget cuts starting in FY1967 gutted the program. Johnson prioritized Great Society and Vietnam.","category":"infrastructure"},
    {"proposed_year":1970,"country":"US","mission":"Big Gemini (Big G)","description":"A 12-person crew ferry scaled up from the proven Gemini spacecraft, reusable for multiple flights.","what_if":"The US would have had a low-cost, proven crew ferry by the early 1970s, avoiding the massive Shuttle development program.","cancelled_reason":"Eliminated 1971 when NASA committed to the Space Shuttle concept.","category":"crewed"},
    {"proposed_year":1970,"country":"USSR","mission":"Voskhod All-Female EVA","description":"An all-female crew mission featuring the first spacewalk by women cosmonauts, following up Tereshkova's 1963 flight.","what_if":"A Soviet female EVA in 1966 would have preceded the first American female astronaut by nearly two decades.","cancelled_reason":"Cancelled with the Voskhod program in 1966 when resources were redirected to Soyuz.","category":"crewed"},
    {"proposed_year":1967,"country":"US","mission":"Apollo Crewed Venus Flyby","description":"A three-person crew on a 400-day flyby past Venus using modified Apollo hardware and a large living module.","what_if":"Mankind's first visit to another planet\u2014an achievement arguably more dramatic than the Moon landing in terms of interplanetary reach.","cancelled_reason":"Never funded. The AAP was gutted by budget cuts and the 1973 launch window became impossible.","category":"crewed"},
    {"proposed_year":1975,"country":"USSR","mission":"L3M / N1F Enhanced Lunar","description":"An upgraded N1F rocket with reliable NK-33 engines, landing two cosmonauts on the Moon for a 30-day stay.","what_if":"Soviet engineers believed the N1F would have succeeded. A dual-cosmonaut 30-day surface stay would have dramatically surpassed Apollo's longest 75-hour stay.","cancelled_reason":"Cancelled 1974 when Glushko replaced Mishin and ordered destruction of all N1 hardware.","category":"crewed"},
    {"proposed_year":1980,"country":"USSR","mission":"Soviet Crewed Mars (MEK)","description":"A 630-day crewed Mars mission for 3-6 cosmonauts using nuclear electric propulsion assembled from multiple heavy-lift launches.","what_if":"Soviet cosmonauts landing on Mars would have been the defining moment of the 20th century, eclipsing the Moon landings.","cancelled_reason":"Never advanced to program status. Soviet economy was structurally incapable of sustaining the cost.","category":"crewed"}
  ];

  const PHOTOS = {
    "Sputnik 1": "https://upload.wikimedia.org/wikipedia/commons/b/be/Sputnik_asm.jpg",
    "Sputnik 2": "https://upload.wikimedia.org/wikipedia/commons/9/9f/Laika_experimental_space_dog_space_suit.jpg",
    "Explorer 1": "https://images-assets.nasa.gov/image/PIA04601/PIA04601~medium.jpg",
    "Vostok 1": "https://upload.wikimedia.org/wikipedia/commons/e/e5/Yuri_Gagarin_%281961%29_-_Restoration.jpg",
    "Mercury-Redstone 3 (Freedom 7)": "https://images-assets.nasa.gov/image/S61-02757/S61-02757~medium.jpg",
    "Mercury-Atlas 6 (Friendship 7)": "https://images-assets.nasa.gov/image/9139490/9139490~medium.jpg",
    "Vostok 6": "https://upload.wikimedia.org/wikipedia/commons/6/61/RIAN_archive_612748_Valentina_Tereshkova.jpg",
    "Voskhod 2": "https://upload.wikimedia.org/wikipedia/commons/f/f8/Alexei_Leonov.jpg",
    "Gemini IV": "https://images-assets.nasa.gov/image/s65-30432/s65-30432~medium.jpg",
    "Gemini VI-A": "https://images-assets.nasa.gov/image/s65-63197/s65-63197~medium.jpg",
    "Gemini VII": "https://images-assets.nasa.gov/image/s65-63197/s65-63197~medium.jpg",
    "Apollo 1": "https://images-assets.nasa.gov/image/S66-30236/S66-30236~medium.jpg",
    "Soyuz 1": "https://upload.wikimedia.org/wikipedia/commons/2/2e/Kosmonavt_Komarov_honouring.jpg",
    "Apollo 8": "https://upload.wikimedia.org/wikipedia/commons/a/a8/NASA-Apollo8-Dec24-Earthrise.jpg",
    "Apollo 11": "https://images-assets.nasa.gov/image/as11-40-5874/as11-40-5874~medium.jpg",
    "Apollo 13": "https://images-assets.nasa.gov/image/S70-17646/S70-17646~medium.jpg",
    "Apollo-Soyuz Test Project": "https://images-assets.nasa.gov/image/s75-29432/s75-29432~medium.jpg",
    "Skylab": "https://images-assets.nasa.gov/image/sl3-114-1682/sl3-114-1682~medium.jpg",
    "Apollo 4 (Saturn V first flight)": "https://images-assets.nasa.gov/image/6864722/6864722~medium.jpg",
    "N1 Rocket - First Test (3L)": "https://upload.wikimedia.org/wikipedia/commons/d/d3/N1_1M1_mockup_on_the_launch_pad_at_the_Baikonur_Cosmodrome_in_late_1967.jpg",
    "N1 Rocket - Second Test (5L)": "https://upload.wikimedia.org/wikipedia/commons/d/d3/N1_1M1_mockup_on_the_launch_pad_at_the_Baikonur_Cosmodrome_in_late_1967.jpg",
    "N1 Rocket - Third Test (6L)": "https://upload.wikimedia.org/wikipedia/commons/d/d3/N1_1M1_mockup_on_the_launch_pad_at_the_Baikonur_Cosmodrome_in_late_1967.jpg",
    "N1 Rocket - Fourth Test (7L)": "https://upload.wikimedia.org/wikipedia/commons/d/d3/N1_1M1_mockup_on_the_launch_pad_at_the_Baikonur_Cosmodrome_in_late_1967.jpg",
    "Luna 16": "https://upload.wikimedia.org/wikipedia/commons/e/e5/Luna_sample_return_and_Lunokhod_lunar_rover_models.jpg",
    "Luna 17 / Lunokhod 1": "https://upload.wikimedia.org/wikipedia/commons/e/e5/Luna_sample_return_and_Lunokhod_lunar_rover_models.jpg"
  };

  // ============================================
  // CONFIGURATION
  // ============================================

  const START_YEAR = 1957;
  const END_YEAR = 1976;
  const PIXELS_PER_YEAR = Math.max(window.innerWidth * 0.55, 500);
  const PADDING_LEFT = Math.max(window.innerWidth * 0.15, 100);
  const PADDING_RIGHT = Math.max(window.innerWidth * 0.3, 200);
  const TOTAL_WIDTH = PADDING_LEFT + (END_YEAR - START_YEAR) * PIXELS_PER_YEAR + PADDING_RIGHT;

  const ERAS = [
    { label: 'The Satellite Race', start: 1957, end: 1960 },
    { label: 'First Humans', start: 1961, end: 1963 },
    { label: 'Gemini & Voskhod', start: 1964, end: 1966 },
    { label: 'Tragedy & Recovery', start: 1967, end: 1968 },
    { label: 'The Moon Race', start: 1969, end: 1969 },
    { label: 'After Apollo', start: 1970, end: 1975 }
  ];

  // ============================================
  // STATE
  // ============================================

  let scrollX = 0;
  let targetScrollX = 0;
  let isDragging = false;
  let dragStartX = 0;
  let dragStartScrollX = 0;
  let whatIfActive = false;
  let expandedEvent = null;
  let animFrame = null;
  let starOffsetX = 0;

  // ============================================
  // UTILITY
  // ============================================

  function dateToX(dateStr) {
    const d = new Date(dateStr + 'T00:00:00Z');
    const yearFrac = d.getUTCFullYear() + (d.getUTCMonth() / 12) + (d.getUTCDate() / 365);
    return PADDING_LEFT + (yearFrac - START_YEAR) * PIXELS_PER_YEAR;
  }

  function yearToX(year) {
    return PADDING_LEFT + (year - START_YEAR) * PIXELS_PER_YEAR;
  }

  function clampScroll(val) {
    const viewportWidth = window.innerWidth;
    const maxScroll = TOTAL_WIDTH - viewportWidth;
    return Math.max(0, Math.min(val, maxScroll));
  }

  function formatDate(dateStr) {
    const d = new Date(dateStr + 'T00:00:00Z');
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[d.getUTCMonth()]} ${d.getUTCDate()}, ${d.getUTCFullYear()}`;
  }

  function countrySymbol(country) {
    return country === 'US' ? '\u{1F1FA}\u{1F1F8}' : '\u2606';
  }

  // ============================================
  // STAR FIELD
  // ============================================

  const canvas = document.getElementById('star-canvas');
  const ctx = canvas.getContext('2d');
  let stars = [];

  function initStars() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    stars = [];
    const count = Math.floor((canvas.width * canvas.height) / 2500);
    for (let i = 0; i < count; i++) {
      stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 1.5 + 0.3,
        brightness: Math.random() * 0.6 + 0.2,
        twinkleSpeed: Math.random() * 0.02 + 0.005,
        twinkleOffset: Math.random() * Math.PI * 2
      });
    }
  }

  function drawStars(time) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const parallaxShift = starOffsetX * 0.05;
    for (const star of stars) {
      const twinkle = Math.sin(time * star.twinkleSpeed + star.twinkleOffset) * 0.3 + 0.7;
      const alpha = star.brightness * twinkle;
      const sx = ((star.x - parallaxShift) % canvas.width + canvas.width) % canvas.width;
      ctx.beginPath();
      ctx.arc(sx, star.y, star.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(200, 210, 230, ${alpha})`;
      ctx.fill();
    }
  }

  // ============================================
  // BUILD TIMELINE
  // ============================================

  const container = document.getElementById('timeline-container');
  const trackUS = document.getElementById('track-us');
  const trackUSSR = document.getElementById('track-ussr');
  const ruler = document.getElementById('timeline-ruler');
  const viewport = document.querySelector('.timeline-viewport');

  container.style.width = TOTAL_WIDTH + 'px';

  // --- Year markers and era labels ---
  for (let y = START_YEAR; y <= 1975; y++) {
    const x = yearToX(y);
    const marker = document.createElement('div');
    marker.className = 'year-marker';
    marker.style.left = x + 'px';
    marker.innerHTML = `<div class="year-tick"></div><div class="year-label">${y}</div>`;
    ruler.appendChild(marker);
  }

  for (const era of ERAS) {
    const midYear = (era.start + era.end) / 2;
    const x = yearToX(midYear);
    const label = document.createElement('div');
    label.className = 'era-label';
    label.style.left = x + 'px';
    label.textContent = era.label;
    ruler.appendChild(label);
  }

  // --- Collision detection for card stacking ---
  function layoutCards(events, track) {
    // Sort by date
    const sorted = [...events].sort((a, b) => new Date(a.date || (a.proposed_year + '-06-15')) - new Date(b.date || (b.proposed_year + '-06-15')));
    const lanes = []; // each lane is an array of {left, right}

    const placements = [];
    for (const ev of sorted) {
      const x = ev.date ? dateToX(ev.date) : yearToX(ev.proposed_year);
      const cardW = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--card-width')) || 280;
      const left = x - cardW / 2;
      const right = x + cardW / 2;

      let laneIdx = 0;
      for (let i = 0; i < lanes.length; i++) {
        const lastInLane = lanes[i][lanes[i].length - 1];
        if (left > lastInLane.right + 16) {
          laneIdx = i;
          break;
        }
        laneIdx = i + 1;
      }

      if (!lanes[laneIdx]) lanes[laneIdx] = [];
      lanes[laneIdx].push({ left, right });
      placements.push({ event: ev, x, laneIdx });
    }

    return { placements, laneCount: lanes.length };
  }

  // Separate events by country
  const usEvents = EVENTS.filter(e => e.country === 'US');
  const ussrEvents = EVENTS.filter(e => e.country === 'USSR');
  const usWhatIf = WHATIF.filter(e => e.country === 'US');
  const ussrWhatIf = WHATIF.filter(e => e.country === 'USSR');

  const usLayout = layoutCards(usEvents, 'us');
  const ussrLayout = layoutCards(ussrEvents, 'ussr');

  // Compute card height based on lane count
  const cardElements = [];

  function createCard(ev, x, laneIdx, laneCount, track, isWhatIf) {
    const country = ev.country.toLowerCase();
    const card = document.createElement('div');
    const classes = ['event-card', country];
    if (!ev.success && !isWhatIf) classes.push('failure');
    if (isWhatIf) classes.push('whatif');
    if (ev.category === 'failure') classes.push('failure');
    card.className = classes.join(' ');

    const cardW = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--card-width')) || 280;
    card.style.left = (x - cardW / 2) + 'px';

    // Position within track
    const trackPadding = 12;
    const cardH = isWhatIf ? 90 : 100;
    const gap = 8;
    if (track === 'us') {
      // Cards go from top downward
      card.style.top = (trackPadding + laneIdx * (cardH + gap)) + 'px';
    } else {
      // Cards go from top downward
      card.style.top = (trackPadding + laneIdx * (cardH + gap)) + 'px';
    }

    const countryIcon = countrySymbol(ev.country);
    const categoryBadge = `badge-${ev.category || 'crewed'}`;
    const dateStr = ev.date ? formatDate(ev.date) : ev.proposed_year;

    card.innerHTML = `
      <div class="card-header">
        <div>
          <div class="card-date">${dateStr}</div>
          <div class="card-mission">${ev.mission}</div>
        </div>
        <span class="card-country">${countryIcon}</span>
      </div>
      <div class="card-badges">
        <span class="badge ${categoryBadge}">${ev.category}</span>
        ${isWhatIf ? '<span class="badge badge-cancelled">CANCELLED</span>' : ''}
        ${!isWhatIf && ev.success !== undefined ? `<span class="success-indicator ${ev.success ? 'success' : 'failed'}">${ev.success ? '✓' : '✕'}</span>` : ''}
      </div>
    `;

    card.addEventListener('click', () => openExpandedCard(ev, isWhatIf));
    card.setAttribute('tabindex', '0');
    card.setAttribute('role', 'button');
    card.setAttribute('aria-label', `${ev.mission} - ${dateStr}`);
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openExpandedCard(ev, isWhatIf);
      }
    });

    return card;
  }

  // Render real events
  for (const { event, x, laneIdx } of usLayout.placements) {
    const card = createCard(event, x, laneIdx, usLayout.laneCount, 'us', false);
    trackUS.appendChild(card);
    cardElements.push({ card, x, isWhatIf: false });

    // Dot on ruler
    const dot = document.createElement('div');
    dot.className = 'event-dot us';
    dot.style.left = x + 'px';
    ruler.appendChild(dot);
  }

  for (const { event, x, laneIdx } of ussrLayout.placements) {
    const card = createCard(event, x, laneIdx, ussrLayout.laneCount, 'ussr', false);
    trackUSSR.appendChild(card);
    cardElements.push({ card, x, isWhatIf: false });

    const dot = document.createElement('div');
    dot.className = 'event-dot ussr';
    dot.style.left = x + 'px';
    ruler.appendChild(dot);
  }

  // Render what-if events
  const usWhatIfLayout = layoutCards(usWhatIf.map(e => ({...e, date: e.proposed_year + '-06-15'})), 'us');
  const ussrWhatIfLayout = layoutCards(ussrWhatIf.map(e => ({...e, date: e.proposed_year + '-06-15'})), 'ussr');

  for (let i = 0; i < usWhatIfLayout.placements.length; i++) {
    const { x, laneIdx } = usWhatIfLayout.placements[i];
    const ev = usWhatIf[i];
    // Offset from real cards
    const card = createCard(ev, x, usLayout.laneCount + laneIdx, usLayout.laneCount + usWhatIfLayout.laneCount, 'us', true);
    trackUS.appendChild(card);
    cardElements.push({ card, x, isWhatIf: true });

    const dot = document.createElement('div');
    dot.className = 'event-dot whatif';
    dot.style.left = x + 'px';
    ruler.appendChild(dot);
  }

  for (let i = 0; i < ussrWhatIfLayout.placements.length; i++) {
    const { x, laneIdx } = ussrWhatIfLayout.placements[i];
    const ev = ussrWhatIf[i];
    const card = createCard(ev, x, ussrLayout.laneCount + laneIdx, ussrLayout.laneCount + ussrWhatIfLayout.laneCount, 'ussr', true);
    trackUSSR.appendChild(card);
    cardElements.push({ card, x, isWhatIf: true });

    const dot = document.createElement('div');
    dot.className = 'event-dot whatif';
    dot.style.left = x + 'px';
    ruler.appendChild(dot);
  }

  // ============================================
  // MINIMAP
  // ============================================

  const minimapTrack = document.getElementById('minimap-track');
  const minimapViewport = document.getElementById('minimap-viewport');
  const minimap = document.getElementById('minimap');

  // Minimap year labels
  for (let y = START_YEAR; y <= 1975; y += 3) {
    const pct = (yearToX(y) / TOTAL_WIDTH) * 100;
    const label = document.createElement('div');
    label.className = 'minimap-year';
    label.style.left = pct + '%';
    label.textContent = y;
    minimapTrack.appendChild(label);
  }

  // Minimap event dots
  for (const ev of EVENTS) {
    const x = dateToX(ev.date);
    const pct = (x / TOTAL_WIDTH) * 100;
    const dot = document.createElement('div');
    dot.className = 'minimap-event ' + ev.country.toLowerCase();
    dot.style.left = pct + '%';
    minimapTrack.appendChild(dot);
  }

  function updateMinimap() {
    const vw = window.innerWidth;
    const pctLeft = (scrollX / TOTAL_WIDTH) * 100;
    const pctWidth = (vw / TOTAL_WIDTH) * 100;
    minimapViewport.style.left = pctLeft + '%';
    minimapViewport.style.width = pctWidth + '%';
  }

  minimap.addEventListener('click', (e) => {
    const rect = minimapTrack.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    targetScrollX = clampScroll(pct * TOTAL_WIDTH - window.innerWidth / 2);
  });

  // ============================================
  // SCROLLING & PANNING
  // ============================================

  // Mouse wheel → horizontal scroll
  viewport.addEventListener('wheel', (e) => {
    e.preventDefault();
    const delta = Math.abs(e.deltaY) > Math.abs(e.deltaX) ? e.deltaY : e.deltaX;
    targetScrollX = clampScroll(targetScrollX + delta * 1.5);
  }, { passive: false });

  // Click and drag
  viewport.addEventListener('mousedown', (e) => {
    isDragging = true;
    dragStartX = e.clientX;
    dragStartScrollX = targetScrollX;
    viewport.classList.add('dragging');
  });

  window.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const dx = dragStartX - e.clientX;
    targetScrollX = clampScroll(dragStartScrollX + dx);
  });

  window.addEventListener('mouseup', () => {
    isDragging = false;
    viewport.classList.remove('dragging');
  });

  // Touch support
  let touchStartX = 0;
  let touchStartScrollX = 0;

  viewport.addEventListener('touchstart', (e) => {
    touchStartX = e.touches[0].clientX;
    touchStartScrollX = targetScrollX;
  }, { passive: true });

  viewport.addEventListener('touchmove', (e) => {
    const dx = touchStartX - e.touches[0].clientX;
    targetScrollX = clampScroll(touchStartScrollX + dx);
  }, { passive: true });

  // Keyboard
  document.addEventListener('keydown', (e) => {
    if (expandedEvent) {
      if (e.key === 'Escape') closeExpandedCard();
      return;
    }
    if (e.key === 'ArrowRight') {
      targetScrollX = clampScroll(targetScrollX + 300);
    } else if (e.key === 'ArrowLeft') {
      targetScrollX = clampScroll(targetScrollX - 300);
    }
  });

  // ============================================
  // ANIMATION LOOP
  // ============================================

  let lastTime = 0;

  function animate(time) {
    animFrame = requestAnimationFrame(animate);

    // Smooth scroll interpolation
    scrollX += (targetScrollX - scrollX) * 0.12;
    if (Math.abs(targetScrollX - scrollX) < 0.5) scrollX = targetScrollX;

    container.style.transform = `translateX(${-scrollX}px)`;
    starOffsetX = scrollX;

    // Draw stars
    drawStars(time * 0.001);

    // Update minimap
    updateMinimap();

    // Update stats based on visible events
    updateStats();

    // Animate cards into view
    animateCardsIn();
  }

  // ============================================
  // ENTRY ANIMATIONS
  // ============================================

  function animateCardsIn() {
    const vw = window.innerWidth;
    const viewLeft = scrollX - 200;
    const viewRight = scrollX + vw + 200;

    for (const { card, x, isWhatIf } of cardElements) {
      if (x >= viewLeft && x <= viewRight) {
        if (!card.classList.contains('animate-in')) {
          card.classList.add('animate-in');
        }
      }
    }
  }

  // ============================================
  // STATS COUNTER
  // ============================================

  const statMissions = document.getElementById('stat-missions');
  const statFailures = document.getElementById('stat-failures');
  const statFirsts = document.getElementById('stat-firsts');
  const statMissionsLabel = document.getElementById('stat-missions-label');
  const statFailuresLabel = document.getElementById('stat-failures-label');
  const statFirstsLabel = document.getElementById('stat-firsts-label');

  function updateStats() {
    const vw = window.innerWidth;
    const viewRight = scrollX + vw;

    let missions = 0;
    let failures = 0;
    let firsts = 0;

    for (const ev of EVENTS) {
      const x = dateToX(ev.date);
      if (x <= viewRight + 100) {
        missions++;
        if (!ev.success) failures++;
        if (ev.category === 'milestone') firsts++;
      }
    }

    statMissions.textContent = missions;
    statFailures.textContent = failures;
    statFirsts.textContent = firsts;
    statMissionsLabel.textContent = missions === 1 ? 'mission' : 'missions';
    statFailuresLabel.textContent = failures === 1 ? 'failure' : 'failures';
    statFirstsLabel.textContent = firsts === 1 ? 'first' : 'firsts';
  }

  // ============================================
  // WHAT IF TOGGLE
  // ============================================

  const whatifToggle = document.getElementById('whatif-toggle');

  whatifToggle.addEventListener('click', () => {
    whatIfActive = !whatIfActive;
    whatifToggle.classList.toggle('active', whatIfActive);
    whatifToggle.setAttribute('aria-pressed', whatIfActive);

    const whatifCards = document.querySelectorAll('.event-card.whatif');
    const whatifDots = document.querySelectorAll('.event-dot.whatif');

    whatifCards.forEach((card, i) => {
      setTimeout(() => {
        card.classList.toggle('visible', whatIfActive);
      }, i * 40);
    });

    whatifDots.forEach((dot, i) => {
      setTimeout(() => {
        dot.classList.toggle('visible', whatIfActive);
      }, i * 30);
    });
  });

  // ============================================
  // EXPANDED CARD
  // ============================================

  const overlay = document.getElementById('card-overlay');
  const expandedCard = document.getElementById('expanded-card');
  const expandedContent = document.getElementById('expanded-content');

  function openExpandedCard(ev, isWhatIf) {
    expandedEvent = ev;
    const country = ev.country.toLowerCase();

    expandedCard.className = 'expanded-card ' + country;
    if (isWhatIf) expandedCard.className += ' whatif';

    const photo = PHOTOS[ev.mission];
    const dateStr = ev.date ? formatDate(ev.date) : `Proposed: ${ev.proposed_year}`;
    const countryIcon = countrySymbol(ev.country);
    const categoryBadge = `badge-${ev.category || 'crewed'}`;

    let html = '';

    if (photo) {
      html += `<img class="expanded-photo" src="${photo}" alt="${ev.mission}" loading="lazy" decoding="async" onerror="this.style.display='none'">`;
    }

    html += `<div class="expanded-body">`;
    html += `<div class="card-date">${countryIcon} ${dateStr}</div>`;
    html += `<div class="card-mission">${ev.mission}</div>`;
    html += `<p class="card-description">${ev.description}</p>`;
    html += `<div class="card-badges">`;
    html += `<span class="badge ${categoryBadge}">${ev.category}</span>`;

    if (isWhatIf) {
      html += `<span class="badge badge-cancelled">CANCELLED</span>`;
    } else if (ev.success !== undefined) {
      html += `<span class="success-indicator ${ev.success ? 'success' : 'failed'}">${ev.success ? '✓ Success' : '✕ Failed'}</span>`;
    }

    html += `</div>`;

    if (isWhatIf && ev.what_if) {
      html += `<div class="whatif-section">`;
      html += `<h4>What If?</h4>`;
      html += `<p>${ev.what_if}</p>`;
      html += `</div>`;
    }

    if (isWhatIf && ev.cancelled_reason) {
      html += `<div class="whatif-section cancelled-reason">`;
      html += `<h4>Why It Was Cancelled</h4>`;
      html += `<p>${ev.cancelled_reason}</p>`;
      html += `</div>`;
    }

    html += `</div>`;

    expandedContent.innerHTML = html;
    overlay.classList.add('visible');
    overlay.setAttribute('aria-hidden', 'false');

    // Focus the close button
    setTimeout(() => {
      expandedCard.querySelector('.close-btn').focus();
    }, 100);
  }

  function closeExpandedCard() {
    expandedEvent = null;
    overlay.classList.remove('visible');
    overlay.setAttribute('aria-hidden', 'true');
  }

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeExpandedCard();
  });

  expandedCard.querySelector('.close-btn').addEventListener('click', closeExpandedCard);

  // ============================================
  // INIT
  // ============================================

  function init() {
    initStars();

    // Start scrolled to 1957
    targetScrollX = 0;
    scrollX = 0;

    // Start animation loop
    requestAnimationFrame(animate);

    // Handle resize
    window.addEventListener('resize', () => {
      initStars();
      updateMinimap();
    });
  }

  init();

})();
