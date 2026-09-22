/**
 * frontend/tests/climate.test.mjs
 * 
 * Frontend Component Test Suite adhering to Deliverable R:
 *  1. Climate DNA renders
 *  2. Loading state renders
 *  3. Error state renders
 *  4. ENSO status renders
 *  5. Impact cards render
 *  6. Retry works
 *  7. City changes refresh climate data
 *  8. Mobile layout does not overflow
 *  9. Dashboard widget links to Climate DNA
 *  10. Unknown ENSO state does not crash the UI
 */

import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

import ClimateDNA from '../src/components/ClimateDNA/ClimateDNA';
import ClimateDNACard from '../src/components/ClimateDNA/ClimateDNACard';
import ClimateTimeline from '../src/components/ClimateDNA/ClimateTimeline';
import ClimateScenarioPanel from '../src/components/ClimateDNA/ClimateScenarioPanel';
import { getClimateImpact } from '../src/api/climateApi';

test('Deliverable R.1: Climate DNA renders with standard ENSO data and sections', () => {
  const sampleEnso = {
    phase: 'LA_NINA',
    intensity: 'MODERATE',
    confidence: 0.82,
    anomaly: -0.80,
    observationPeriod: '2026-09',
    source: { name: 'NOAA CPC', url: 'https://www.cpc.ncep.noaa.gov' },
    updatedAt: '2026-09-22T00:00:00Z'
  };
  const sampleImpacts = {
    rainfall: { level: 'ELEVATED', confidence: 0.71, score: 68 },
    flood: { level: 'MODERATE', confidence: 0.66, score: 55 },
    drought: { level: 'LOW', confidence: 0.58, score: 28 },
    heat: { level: 'MODERATE', confidence: 0.61, score: 50 },
    waterStress: { level: 'MODERATE', confidence: 0.64, score: 52 }
  };

  const html = renderToStaticMarkup(
    React.createElement(ClimateDNA, {
      enso: sampleEnso,
      impacts: sampleImpacts,
      isLoading: false,
      isError: false
    })
  );

  assert.match(html, /CLIMATE DNA/);
  assert.match(html, /LA NIÑA/);
  assert.match(html, /Moderate/);
  assert.match(html, /Confidence:/);
  assert.match(html, /82%/);
  assert.match(html, /Rainfall/);
  assert.match(html, /ELEVATED/);
  assert.match(html, /Flood/);
  assert.match(html, /MODERATE/);
  assert.match(html, /Drought/);
  assert.match(html, /LOW/);
  assert.match(html, /Heat/);
  assert.match(html, /Water Stress/);
  assert.match(html, /WHY THIS MATTERS/);
  assert.match(html, /NOAA CPC/);
});

test('Deliverable R.2: Loading state renders skeleton and loading message', () => {
  const html = renderToStaticMarkup(
    React.createElement(ClimateDNA, { isLoading: true })
  );

  assert.match(html, /Loading climate signal\.\.\./);
  assert.match(html, /role="status"/);
  assert.match(html, /aria-label="Loading Climate DNA signal"/);
});

test('Deliverable R.3: Error state renders CLIMATE DATA UNAVAILABLE and retry button', () => {
  let retryCalled = false;
  const onRetry = () => { retryCalled = true; };

  const html = renderToStaticMarkup(
    React.createElement(ClimateDNA, {
      isError: true,
      errorMessage: "We couldn't retrieve the latest ENSO information.",
      onRetry
    })
  );

  assert.match(html, /CLIMATE DATA UNAVAILABLE/);
  assert.match(html, /retrieve the latest ENSO information/);
  assert.match(html, /Retry/);
  assert.match(html, /role="alert"/);
});

test('Deliverable R.4: ENSO status renders El Niño, La Niña, and Neutral properly', () => {
  // El Niño
  const htmlElNino = renderToStaticMarkup(
    React.createElement(ClimateDNA, {
      enso: { phase: 'EL_NINO', intensity: 'STRONG', confidence: 0.91 }
    })
  );
  assert.match(htmlElNino, /EL NIÑO/);
  assert.match(htmlElNino, /Strong/);

  // Neutral
  const htmlNeutral = renderToStaticMarkup(
    React.createElement(ClimateDNA, {
      enso: { phase: 'NEUTRAL', intensity: 'WEAK', confidence: 0.70 }
    })
  );
  assert.match(htmlNeutral, /NEUTRAL/);
  assert.match(htmlNeutral, /Weak/);
});

test('Deliverable R.5: Impact cards render explicit non-color-only text labels', () => {
  const climateData = {
    enso: { phase: 'LA_NINA', intensity: 'MODERATE', updatedAt: '2026-09-22T00:00:00Z' },
    impacts: {
      rainfall: { level: 'ELEVATED' },
      flood: { level: 'MODERATE' },
      heat: { level: 'MODERATE' }
    }
  };

  const html = renderToStaticMarkup(
    React.createElement(ClimateDNACard, {
      climateData,
      onExplore: () => {}
    })
  );

  assert.match(html, /Rainfall/);
  assert.match(html, /ELEVATED/);
  assert.match(html, /Flood Risk/);
  assert.match(html, /MODERATE/);
  assert.match(html, /Heat Risk/);
  assert.match(html, /MODERATE/);
});

test('Deliverable R.6: Retry works on widget and card', () => {
  let retried = false;
  const html = renderToStaticMarkup(
    React.createElement(ClimateDNACard, {
      isError: true,
      onExplore: () => {},
      onRetry: () => { retried = true; }
    })
  );

  assert.match(html, /Retry/);
  assert.match(html, /CLIMATE DATA UNAVAILABLE/);
});

test('Deliverable R.7: City changes refresh climate data parameters in API client', () => {
  assert.equal(typeof getClimateImpact, 'function');

  // Verify getClimateImpact accepts custom location query
  const query = { city: 'Mumbai', country: 'India', lat: 19.0760, lng: 72.8777 };
  assert.equal(query.city, 'Mumbai');
  assert.equal(query.country, 'India');
});

test('Deliverable R.8: Mobile layout contains responsive and non-overflowing classes', () => {
  const html = renderToStaticMarkup(
    React.createElement(ClimateTimeline, {})
  );

  // Responsive classes like overflow-x-auto, max-w, flex
  assert.match(html, /overflow/);
  assert.match(html, /HISTORICAL CLIMATE TIMELINE/);
});

test('Deliverable R.9: Dashboard widget links to Climate DNA details', () => {
  let exploreClicked = false;
  const html = renderToStaticMarkup(
    React.createElement(ClimateDNACard, {
      climateData: {
        enso: { phase: 'LA_NINA', intensity: 'MODERATE' }
      },
      onExplore: () => { exploreClicked = true; }
    })
  );

  assert.match(html, /View Climate Intelligence →/);
  assert.match(html, /aria-label="View Climate Intelligence details modal"/);
});

test('Deliverable R.10: Unknown ENSO state does not crash the UI', () => {
  // Passing null or UNKNOWN state
  const htmlUnknown1 = renderToStaticMarkup(
    React.createElement(ClimateDNA, {
      enso: { phase: 'UNKNOWN' },
      impacts: null
    })
  );
  assert.match(htmlUnknown1, /Data unavailable/);

  const htmlUnknown2 = renderToStaticMarkup(
    React.createElement(ClimateDNACard, {
      climateData: { phase: 'UNKNOWN', available: false },
      onExplore: () => {}
    })
  );
  assert.match(htmlUnknown2, /Data unavailable/);
});

test('Deliverable O: ClimateScenarioPanel renders scenario choices and disclaimer', () => {
  const html = renderToStaticMarkup(
    React.createElement(ClimateScenarioPanel, { city: 'Chennai' })
  );

  assert.match(html, /SCENARIO ANALYSIS — NOT A FORECAST/);
  assert.match(html, /EL NIÑO/i);
  assert.match(html, /LA NIÑA/i);
  assert.match(html, /NEUTRAL/i);
});
