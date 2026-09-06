/**
 * Tests: Multi-Market Canonical Helpers, Formatting & Data Freshness
 * Self-contained executable verification suite.
 */

import { parseSecurityId, buildSecurityId, getDataFreshnessInfo, SUPPORTED_MARKETS_CONFIG } from "../market";
import { formatCurrency, formatPercent, formatLargeNumber } from "../formatting";

export function runMultiMarketTests(): { passed: number; failed: number; errors: string[] } {
  let passed = 0;
  let failed = 0;
  const errors: string[] = [];

  function assert(condition: boolean, msg: string) {
    if (condition) {
      passed++;
    } else {
      failed++;
      errors.push(msg);
      console.error(`❌ TEST FAILED: ${msg}`);
    }
  }

  // 1. Canonical Resolution
  const pk = parseSecurityId("PK.PSX.ENGRO");
  assert(pk.marketCode === "PK", "PK marketCode should be PK");
  assert(pk.exchangeCode === "PSX", "PK exchangeCode should be PSX");
  assert(pk.ticker === "ENGRO", "PK ticker should be ENGRO");
  assert(pk.canonicalId === "PK.PSX.ENGRO", "PK canonicalId matches");

  const us = parseSecurityId("US.NASDAQ.AAPL");
  assert(us.marketCode === "US", "US marketCode should be US");
  assert(us.exchangeCode === "NASDAQ", "US exchangeCode should be NASDAQ");
  assert(us.ticker === "AAPL", "US ticker should be AAPL");
  assert(us.canonicalId === "US.NASDAQ.AAPL", "US canonicalId matches");

  const uk = parseSecurityId("AZN.L");
  assert(uk.marketCode === "UK", "UK marketCode resolved from .L suffix");
  assert(uk.exchangeCode === "LSE", "UK exchangeCode is LSE");

  const jp = parseSecurityId("7203.T");
  assert(jp.marketCode === "JP", "JP marketCode resolved from .T suffix");
  assert(jp.exchangeCode === "TSE", "JP exchangeCode is TSE");

  // 2. Build ID
  assert(buildSecurityId("PK", "PSX", "HBL") === "PK.PSX.HBL", "Builds PK.PSX.HBL");
  assert(buildSecurityId("US", "NYSE", "JPM") === "US.NYSE.JPM", "Builds US.NYSE.JPM");

  // 3. Formatting
  const pkrFormatted = formatCurrency(285.5, "PKR");
  assert(pkrFormatted.includes("Rs."), "PKR includes Rs. prefix");
  assert(pkrFormatted.includes("285.50"), "PKR includes 285.50");

  const usdFormatted = formatCurrency(180.25, "USD");
  assert(usdFormatted.includes("$180.25"), "USD includes $180.25");

  assert(formatPercent(5.2) === "+5.20%", "Positive percent has + prefix");
  assert(formatPercent(-3.1) === "-3.10%", "Negative percent has - prefix");
  assert(formatLargeNumber(1_500_000) === "1.50M", "1.5M format");
  assert(formatLargeNumber(2_500_000_000) === "2.50B", "2.5B format");

  // 4. Data Freshness Rules
  const pkFresh = getDataFreshnessInfo("PK");
  assert(pkFresh.status === "LATEST_AVAILABLE_EOD", "PK defaults to LATEST_AVAILABLE_EOD");
  assert(pkFresh.source.includes("PSX"), "PK source mentions PSX");

  const usFresh = getDataFreshnessInfo("US");
  assert(usFresh.status === "DELAYED", "US defaults to DELAYED");

  const liveFresh = getDataFreshnessInfo("US", { is_delayed: false });
  assert(liveFresh.status === "LIVE", "Explicit live quote returns LIVE");

  console.log(`\n🎉 Frontend Test Suite Results: ${passed} passed, ${failed} failed.`);
  if (failed > 0) {
    process.exit(1);
  }

  return { passed, failed, errors };
}

if (typeof require !== "undefined" && require.main === module) {
  runMultiMarketTests();
} else {
  runMultiMarketTests();
}
