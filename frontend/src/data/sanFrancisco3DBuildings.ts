export interface Building3D {
  id: string;
  name: string;
  type: 'skyscraper' | 'commercial' | 'residential' | 'hospital' | 'park' | 'civic';
  coordinates: [number, number][];
  height: number; // in meters
  floors: number;
  power_load_mw: number;
  occupancy: number;
  address: string;
}

// San Francisco Downtown / Financial District High-Fidelity 3D Building Geometry
export const SAN_FRANCISCO_3D_BUILDINGS: Building3D[] = [
  // 1. Salesforce Tower (Tallest building in SF: 326m)
  {
    id: 'sf-salesforce-tower',
    name: 'Salesforce Tower',
    type: 'skyscraper',
    coordinates: [
      [-122.3976, 37.7894],
      [-122.3968, 37.7894],
      [-122.3968, 37.7900],
      [-122.3976, 37.7900],
      [-122.3976, 37.7894],
    ],
    height: 326,
    floors: 61,
    power_load_mw: 8.4,
    occupancy: 4500,
    address: '415 Mission St, Financial District'
  },
  // 2. Transamerica Pyramid (Iconic 260m pyramid spire)
  {
    id: 'sf-transamerica',
    name: 'Transamerica Pyramid',
    type: 'skyscraper',
    coordinates: [
      [-122.4023, 37.7949],
      [-122.4015, 37.7949],
      [-122.4015, 37.7955],
      [-122.4023, 37.7955],
      [-122.4023, 37.7949],
    ],
    height: 260,
    floors: 48,
    power_load_mw: 6.2,
    occupancy: 3200,
    address: '600 Montgomery St, Financial District'
  },
  // 3. 555 California Street (Former Bank of America Center: 237m)
  {
    id: 'sf-555-california',
    name: '555 California Street',
    type: 'skyscraper',
    coordinates: [
      [-122.4046, 37.7922],
      [-122.4038, 37.7922],
      [-122.4038, 37.7928],
      [-122.4046, 37.7928],
      [-122.4046, 37.7922],
    ],
    height: 237,
    floors: 52,
    power_load_mw: 7.1,
    occupancy: 3800,
    address: '555 California St, Financial District'
  },
  // 4. 181 Fremont Tower (245m mixed use luxury/tech)
  {
    id: 'sf-181-fremont',
    name: '181 Fremont Tower',
    type: 'skyscraper',
    coordinates: [
      [-122.3965, 37.7901],
      [-122.3958, 37.7901],
      [-122.3958, 37.7907],
      [-122.3965, 37.7907],
      [-122.3965, 37.7901],
    ],
    height: 245,
    floors: 56,
    power_load_mw: 5.8,
    occupancy: 2900,
    address: '181 Fremont St, SOMA / Transbay'
  },
  // 5. Millennium Tower (197m residential high-rise)
  {
    id: 'sf-millennium-tower',
    name: 'Millennium Tower',
    type: 'residential',
    coordinates: [
      [-122.3962, 37.7911],
      [-122.3955, 37.7911],
      [-122.3955, 37.7917],
      [-122.3962, 37.7917],
      [-122.3962, 37.7911],
    ],
    height: 197,
    floors: 58,
    power_load_mw: 4.6,
    occupancy: 1200,
    address: '301 Mission St, SOMA'
  },
  // 6. Embarcadero Center 1 & 2 (140m - 145m brutalist commercial towers)
  {
    id: 'sf-embarcadero-1',
    name: 'One Embarcadero Center',
    type: 'commercial',
    coordinates: [
      [-122.4001, 37.7950],
      [-122.3993, 37.7950],
      [-122.3993, 37.7956],
      [-122.4001, 37.7956],
      [-122.4001, 37.7950],
    ],
    height: 143,
    floors: 45,
    power_load_mw: 5.2,
    occupancy: 2600,
    address: '1 Embarcadero Center'
  },
  {
    id: 'sf-embarcadero-4',
    name: 'Four Embarcadero Center',
    type: 'commercial',
    coordinates: [
      [-122.3970, 37.7955],
      [-122.3962, 37.7955],
      [-122.3962, 37.7961],
      [-122.3970, 37.7961],
      [-122.3970, 37.7955],
    ],
    height: 174,
    floors: 45,
    power_load_mw: 5.5,
    occupancy: 2800,
    address: '4 Embarcadero Center'
  },
  // 7. San Francisco Ferry Building & Historic Port Tower
  {
    id: 'sf-ferry-building',
    name: 'San Francisco Ferry Building',
    type: 'civic',
    coordinates: [
      [-122.3942, 37.7952],
      [-122.3934, 37.7952],
      [-122.3934, 37.7960],
      [-122.3942, 37.7960],
      [-122.3942, 37.7952],
    ],
    height: 75,
    floors: 4,
    power_load_mw: 2.1,
    occupancy: 1500,
    address: '1 Ferry Building, The Embarcadero'
  },
  // 8. San Francisco City Hall (Historic 94m Beaux-Arts Dome)
  {
    id: 'sf-city-hall',
    name: 'San Francisco City Hall',
    type: 'civic',
    coordinates: [
      [-122.4200, 37.7788],
      [-122.4188, 37.7788],
      [-122.4188, 37.7796],
      [-122.4200, 37.7796],
      [-122.4200, 37.7788],
    ],
    height: 94,
    floors: 4,
    power_load_mw: 3.4,
    occupancy: 1800,
    address: '1 Dr Carlton B Goodlett Pl, Civic Center'
  },
  // 9. Zuckerberg San Francisco General / St. Mary's Medical Hub
  {
    id: 'sf-general-hospital',
    name: 'Metropolitan Trauma & Hospital Center',
    type: 'hospital',
    coordinates: [
      [-122.4080, 37.7755],
      [-122.4068, 37.7755],
      [-122.4068, 37.7765],
      [-122.4080, 37.7765],
      [-122.4080, 37.7755],
    ],
    height: 68,
    floors: 14,
    power_load_mw: 11.2,
    occupancy: 2400,
    address: '1001 Potrero Ave, Medical District'
  },
  // 10. Moscone Convention Center (SOMA)
  {
    id: 'sf-moscone-center',
    name: 'Moscone Convention Center',
    type: 'civic',
    coordinates: [
      [-122.4035, 37.7835],
      [-122.4015, 37.7835],
      [-122.4015, 37.7850],
      [-122.4035, 37.7850],
      [-122.4035, 37.7835],
    ],
    height: 38,
    floors: 3,
    power_load_mw: 4.8,
    occupancy: 6000,
    address: '747 Howard St, SOMA'
  },
  // 11. Salesforce Transit Center & Rooftop Park
  {
    id: 'sf-transit-park',
    name: 'Salesforce Transit Center Rooftop Park',
    type: 'park',
    coordinates: [
      [-122.3995, 37.7888],
      [-122.3955, 37.7888],
      [-122.3955, 37.7896],
      [-122.3995, 37.7896],
      [-122.3995, 37.7888],
    ],
    height: 22,
    floors: 4,
    power_load_mw: 1.5,
    occupancy: 800,
    address: '425 Mission St Rooftop Park'
  },
  // 12. Yerba Buena Gardens & Esplanade
  {
    id: 'sf-yerba-buena',
    name: 'Yerba Buena Cultural Gardens',
    type: 'park',
    coordinates: [
      [-122.4038, 37.7853],
      [-122.4020, 37.7853],
      [-122.4020, 37.7865],
      [-122.4038, 37.7865],
      [-122.4038, 37.7853],
    ],
    height: 12,
    floors: 1,
    power_load_mw: 0.6,
    occupancy: 500,
    address: '750 Howard St, SOMA'
  },
  // 13. SOMA Innovation Tower 1
  {
    id: 'sf-soma-tower-1',
    name: 'SOMA Tech Innovation Center',
    type: 'commercial',
    coordinates: [
      [-122.4060, 37.7870],
      [-122.4050, 37.7870],
      [-122.4050, 37.7878],
      [-122.4060, 37.7878],
      [-122.4060, 37.7870],
    ],
    height: 135,
    floors: 32,
    power_load_mw: 4.2,
    occupancy: 2200,
    address: '2nd & Howard St'
  },
  // 14. Rincon Hill Residential Tower
  {
    id: 'sf-rincon-tower',
    name: 'The Infinity Rincon Hill',
    type: 'residential',
    coordinates: [
      [-122.3925, 37.7895],
      [-122.3915, 37.7895],
      [-122.3915, 37.7903],
      [-122.3925, 37.7903],
      [-122.3925, 37.7895],
    ],
    height: 128,
    floors: 37,
    power_load_mw: 3.1,
    occupancy: 1100,
    address: '300 Spear St, Rincon Hill'
  },
  // 15. Market Street Commercial Spine
  {
    id: 'sf-market-spine',
    name: 'Mid-Market Tech Pavilion',
    type: 'commercial',
    coordinates: [
      [-122.4110, 37.7790],
      [-122.4098, 37.7790],
      [-122.4098, 37.7800],
      [-122.4110, 37.7800],
      [-122.4110, 37.7790],
    ],
    height: 95,
    floors: 24,
    power_load_mw: 3.5,
    occupancy: 1800,
    address: '1355 Market St, Mid-Market'
  },
  // 16. Mission Bay Biotechnology Center
  {
    id: 'sf-mission-bio',
    name: 'Mission Bay Bio-Research Campus',
    type: 'commercial',
    coordinates: [
      [-122.3910, 37.7730],
      [-122.3895, 37.7730],
      [-122.3895, 37.7742],
      [-122.3910, 37.7742],
      [-122.3910, 37.7730],
    ],
    height: 72,
    floors: 8,
    power_load_mw: 6.4,
    occupancy: 1600,
    address: '16th & 4th St, Mission Bay'
  },
  // 17. South Beach Marina Lofts
  {
    id: 'sf-south-beach',
    name: 'South Beach Waterfront Condos',
    type: 'residential',
    coordinates: [
      [-122.3885, 37.7815],
      [-122.3875, 37.7815],
      [-122.3875, 37.7825],
      [-122.3885, 37.7825],
      [-122.3885, 37.7815],
    ],
    height: 48,
    floors: 12,
    power_load_mw: 1.8,
    occupancy: 650,
    address: 'King St Waterfront'
  },
  // 18. Chinatown Cultural Center
  {
    id: 'sf-chinatown-center',
    name: 'Portsmouth Plaza & Cultural Center',
    type: 'civic',
    coordinates: [
      [-122.4055, 37.7940],
      [-122.4045, 37.7940],
      [-122.4045, 37.7948],
      [-122.4055, 37.7948],
      [-122.4055, 37.7940],
    ],
    height: 42,
    floors: 6,
    power_load_mw: 1.4,
    occupancy: 950,
    address: '733 Kearny St, Chinatown'
  },
  // 19. Nob Hill Grand Residential
  {
    id: 'sf-nob-hill',
    name: 'Nob Hill Terrace Suites',
    type: 'residential',
    coordinates: [
      [-122.4120, 37.7925],
      [-122.4108, 37.7925],
      [-122.4108, 37.7935],
      [-122.4120, 37.7935],
      [-122.4120, 37.7925],
    ],
    height: 82,
    floors: 22,
    power_load_mw: 2.5,
    occupancy: 800,
    address: 'California & Mason St'
  },
  // 20. Downtown Substation & Power Switchyard
  {
    id: 'sf-downtown-substation',
    name: 'Downtown Power Substation C',
    type: 'commercial',
    coordinates: [
      [-122.4005, 37.7810],
      [-122.3995, 37.7810],
      [-122.3995, 37.7818],
      [-122.4005, 37.7818],
      [-122.4005, 37.7810],
    ],
    height: 28,
    floors: 2,
    power_load_mw: 32.0,
    occupancy: 45,
    address: 'Mission & 6th Grid Station'
  }
];
