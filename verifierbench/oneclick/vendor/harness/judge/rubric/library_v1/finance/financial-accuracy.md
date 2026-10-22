# finance / Financial Accuracy(1335 条)

## FIN-0001 [必须]
判据: Response acknowledges that private real estate allocation provides partial inflation protection (e.g., through rental income or property value adjustment, partial CPI passthrough).
提示: Recognizing real estate's inflation hedge property informs allocation decisions for protecting user's real returns.
出处: prbench:02db9f46ffd85f56b67cc317 | 话题: Wealth Management, Financial Planning & Advice

## FIN-0002 [必须]
判据: Response acknowledges that the 20% nominal bond allocation offers low real returns under expected inflation (e.g., negative real yield, limited inflation passthrough).
提示: Recognize real return limitations of bonds to justify adjusting allocations for inflation protection.
出处: prbench:02db9f46ffd85f56b67cc317 | 话题: Wealth Management, Financial Planning & Advice

## FIN-0003 [负面]
判据: The response incorrectly advises that check-the-box elections automatically guarantee treaty benefits (e.g., 'Making a check-the-box election ensures the SARL can access France-Luxembourg treaty benefits').
提示: The fundamental misunderstanding that US tax elections affect foreign treaty determinations could result in unexpected withholding taxes.
出处: prbench:049390f8ce786c9cb6464972 | 话题: Taxation & Cross-Border Structuring

## FIN-0004 [负面]
判据: The response incorrectly states that PECs are always treated as debt for French tax purposes (e.g., 'PECs automatically qualify as debt instruments under French law').
提示: Misses core recharacterization risk - hybrid instruments face scrutiny under French thin cap and substance rules.
出处: prbench:049390f8ce786c9cb6464972 | 话题: Taxation & Cross-Border Structuring

## FIN-0005 [必须]
判据: Quantifies the standard French dividend withholding tax rate that would apply if interest is recharacterized (e.g., 'If recharacterized as dividends, payments would face French withholding tax at 12.8% under the France-Luxembourg treaty or 30% under domestic law').
提示: Providing the correct numerical rate is a basic element of a complete financial analysis.
出处: prbench:049390f8ce786c9cb6464972 | 话题: Taxation & Cross-Border Structuring

## FIN-0006 [负面]
判据: The response incorrectly states that disregarded entity status eliminates all French withholding tax risks (e.g., 'Once the SARL is disregarded for US purposes, French withholding tax is no longer a concern').
提示: Serious misconception about tax sovereignty - disregarded status doesn't affect French tax treatment.
出处: prbench:049390f8ce786c9cb6464972 | 话题: Taxation & Cross-Border Structuring

## FIN-0007 [必须]
判据: The response correctly states that interest paid by a French payer to a non-resident is not subject to French withholding tax.
提示: This is the foundational point for any expert analysis; without it, the entire risk assessment is improperly framed.
出处: prbench:049390f8ce786c9cb6464972 | 话题: Taxation & Cross-Border Structuring

## FIN-0008 [必须]
判据: The response calculates daily P&L volatility by multiplying the spread DV01 by spread volatility: σ($) = Spread DV01 × σ(spread), yielding $44,000-$46,500 per day for a $100M position.
提示: Key step connecting volatility to VaR.
出处: prbench:05d0e31487823ecbe68c6fde | 话题: Risk Management & Stress Testing

## FIN-0009 [必须]
判据: The response calculates the P&L impact of a 10bps TED spread widening on the $100M position, yielding approximately a $4,700-$5,100 loss.
提示: Quantifies basis risk through TED shock.
出处: prbench:05d0e31487823ecbe68c6fde | 话题: Risk Management & Stress Testing

## FIN-0010 [必须]
判据: The response calculates the 6-month CD DV01 using the discount factor derivative formula: DV01 = (N × T)/(1+r×T)² × 10⁻⁴, where N = $100M, T = 0.5056, r = 0.0265, yielding $4,750-4,850 per basis point.
提示: Correct derivative formula critical.
出处: prbench:05d0e31487823ecbe68c6fde | 话题: Risk Management & Stress Testing

## FIN-0011 [必须]
判据: The response calculates stressed VaR for the $500M programme, yielding approximately $2.40-2.60 million.
提示: Required for Basel III.
出处: prbench:05d0e31487823ecbe68c6fde | 话题: Risk Management & Stress Testing

## FIN-0012 [必须]
判据: The response calculates initial margin funding cost using: IM Cost = (2% × Futures Notional) × 2.25% × (90/360), yielding $106,000-$110,000 over 3 months.
提示: IM funding cost formula with correct inputs,
出处: prbench:05d0e31487823ecbe68c6fde | 话题: Risk Management & Stress Testing

## FIN-0013 [必须]
判据: The response scales VaR from $100M to $500M by multiplying by 5, yielding $1.60-1.73 million for the programme.
提示: Scaling establishes program-level VaR baseline.
出处: prbench:05d0e31487823ecbe68c6fde | 话题: Risk Management & Stress Testing

## FIN-0014 [必须]
判据: The response calculates the number of Eurodollar futures contracts needed to DV01-hedge the $100M 6-month CD by dividing CD DV01 by $25 per basis point: Contracts = CD_DV01 / $25, yielding 188-195 contracts.
提示: DV01 matching.
出处: prbench:05d0e31487823ecbe68c6fde | 话题: Risk Management & Stress Testing

## FIN-0015 [必须]
判据: The response calculates total futures notional for the $500M programme at approximately $940-$970 million.
提示: Futures notional drives IM cost. Tests hedge ratio understanding.
出处: prbench:05d0e31487823ecbe68c6fde | 话题: Risk Management & Stress Testing

## FIN-0016 [必须]
判据: The response calculates net profit by subtracting initial margin funding cost from the $1.5M gross profit, yielding approximately $1.39-1.40 million.
提示: Tests cost adjustment.
出处: prbench:05d0e31487823ecbe68c6fde | 话题: Risk Management & Stress Testing

## FIN-0017 [必须]
判据: The response calculates risk-weighted assets using the formula: RWA = 12.5 × Economic Capital, where Economic Capital ≈ $4.15M, yielding $50-54M.
提示: RWA shows full regulatory capital impact under Basel III.
出处: prbench:05d0e31487823ecbe68c6fde | 话题: Risk Management & Stress Testing

## FIN-0018 [必须]
判据: The response calculates 3m-6m spread volatility using the correlation formula: σ(spread) = √[σ₆² + σ₃² - 2ρσ₆σ₃], where σ₃ = 15bps, σ₆ = 18bps, ρ = 0.85, yielding 9.40-9.60 bp per day.
提示: Spread volatility is foundation for VaR on hedged positions.
出处: prbench:05d0e31487823ecbe68c6fde | 话题: Risk Management & Stress Testing

## FIN-0019 [必须]
判据: The response states that RAROC for the 3-month period is approximately 30-36%.
提示: Tests full calculation accuracy.
出处: prbench:05d0e31487823ecbe68c6fde | 话题: Risk Management & Stress Testing

## FIN-0020 [必须]
判据: The response calculates total Basel III market risk capital of $4.00-4.30 million for the $500M programme.
提示: Basel III additive formula critical.
出处: prbench:05d0e31487823ecbe68c6fde | 话题: Risk Management & Stress Testing

## FIN-0021 [必须]
判据: The response calculates 10-day 99% VaR of $320,000-$345,000 for the $100M position.
提示: VaR with correct methodology tests full calculation chain accuracy.
出处: prbench:05d0e31487823ecbe68c6fde | 话题: Risk Management & Stress Testing

## FIN-0022 [必须]
判据: The response calculates modified duration using the formula ModDur = T/(1+r×T), where T = 182/360 = 0.5056 and r = 0.0265, yielding 0.4920-0.4935 years.
提示: Correct for money market DV01 derivation.
出处: prbench:05d0e31487823ecbe68c6fde | 话题: Risk Management & Stress Testing

## FIN-0023 [必须]
判据: The response calculates or states the VaR contribution from the 6-month CD leg, expressed in dollars or as a percentage of total VaR.
提示: Advanced risk attribution technique.
出处: prbench:05d0e31487823ecbe68c6fde | 话题: Risk Management & Stress Testing

## FIN-0024 [必须]
判据: The response calculates dollar convexity, yielding $0.45-0.50 per bps².
提示: Dollar convexity formula needed for P&L estimation.
出处: prbench:05d0e31487823ecbe68c6fde | 话题: Risk Management & Stress Testing

## FIN-0025 [必须]
判据: The response states that negotiating short-term debt to long-term debt will improve the current ratio.
提示: Re-negotiation of debt is a key solution to be considered
出处: prbench:06cee946b7fc26947392c088 | 话题: Corporate Finance

## FIN-0026 [必须]
判据: The response states that taking on more long-term debt would improve the current ratio.
提示: A popular solution for public companies facing short term cash crisis is to take on more long-term debt if possible
出处: prbench:06cee946b7fc26947392c088 | 话题: Corporate Finance

## FIN-0027 [必须]
判据: The response calculates that the current ratio is at 0.5:1.0.
提示: The response must be able to understand that the company is in breach and needs to understand by how much
出处: prbench:06cee946b7fc26947392c088 | 话题: Corporate Finance

## FIN-0028 [必须]
判据: The response states that the current ratio is in breach by $3.5M in short-term assets.
提示: The response must be able to understand that the company is in breach and needs to understand by how much
出处: prbench:06cee946b7fc26947392c088 | 话题: Corporate Finance

## FIN-0029 [必须]
判据: The response's dividend repatriation model for the Dutch SPV scenario applies the correct WHT rates to the 1st leg of the cash movement, 0% on Chile-to-NL, per treaty/CIT credit.
提示: This connects the tax analysis to the financial model.
出处: prbench:0855344d17abee65565d8b7d | 话题: Taxation & Cross-Border Structuring

## FIN-0030 [必须]
判据: The response calculates Free Cash Flow to Equity (FCFE) using the standard formula: FCFE = Net Income + Depreciation & Amortisation - Capital Expenditures (Maintenance) - Change in Net Working Capital + Net Borrowing (Debt Issued - Principal Repaid).
提示: The full FCFE formula is a standard requirement for project finance.
出处: prbench:0855344d17abee65565d8b7d | 话题: Taxation & Cross-Border Structuring

## FIN-0031 [建议]
判据: The response's capital structure calculation applies the 60/40 D/E ratio to the $360M CAPEX (0.9M/MW * 400 MW), resulting in a $144M equity value.
提示: Verifies the correct sizing of the initial capital.
出处: prbench:0855344d17abee65565d8b7d | 话题: Taxation & Cross-Border Structuring

## FIN-0032 [必须]
判据: The response's debt split calculation correctly applies the 80/20 ratio to the $216M Total Debt, resulting in a $172.8M Senior Debt allocation.
提示: Verifies the correct allocation of debt.
出处: prbench:0855344d17abee65565d8b7d | 话题: Taxation & Cross-Border Structuring

## FIN-0033 [建议]
判据: The response's dividend repatriation model for the Chilean SpA scenario applies a net dividend WHT rate of 0% per the US-Chile tax treaty.
提示: This connects the tax analysis to the financial model.
出处: prbench:0855344d17abee65565d8b7d | 话题: Taxation & Cross-Border Structuring

## FIN-0034 [必须]
判据: The P&L model(s) reflect the OPEX step-up, using $8 million/year (20,000/MW * 400 MW) for Years 1-4 and $10 million/year (25,000/MW * 400 MW) from Year 5 onwards.
提示: Tests the correct application of the stepped-cost assumption.
出处: prbench:0855344d17abee65565d8b7d | 话题: Taxation & Cross-Border Structuring

## FIN-0035 [建议]
判据: The response's CGT rationale for the Dutch SPV structure references the potential for a 0% tax on gains at the NL level due to the Dutch participation exemption (or deelnemingsvrijstelling).
提示: CGT on exit is a fundamental economic factor.
出处: prbench:0855344d17abee65565d8b7d | 话题: Taxation & Cross-Border Structuring

## FIN-0036 [必须]
判据: The response calculates annual revenue using the prompt's inputs (400 MW, 25% NCF, 8,760 hours/year, 70 USD/MWh), resulting in $61.32 million USD.
提示: Verifies the foundational calculation.
出处: prbench:0855344d17abee65565d8b7d | 话题: Taxation & Cross-Border Structuring

## FIN-0037 [建议]
判据: The response's recommendation is justified by an analysis comparing the net financial advantages (e.g., treaty benefits less compliance costs) of one structure versus the other.
提示: Tests that the justification is linked to the correct factors.
出处: prbench:0855344d17abee65565d8b7d | 话题: Taxation & Cross-Border Structuring

## FIN-0038 [必须]
判据: The response's financial models apply scenario-specific inputs by using a different value for annual ongoing costs (e.g., substance/admin fees) in the Chilean SpA scenario than in the Dutch SPV scenario.
提示: Connecting the tax structure to the model inputs.
出处: prbench:0855344d17abee65565d8b7d | 话题: Taxation & Cross-Border Structuring

## FIN-0039 [必须]
判据: The response includes a debt schedule for the $172.8M Senior Debt that applies the 12-year, 7% fully amortising terms (e.g., an annual payment of approx. $21.76M).
提示: Verifies the correct application of the specified amortising loan terms.
出处: prbench:0855344d17abee65565d8b7d | 话题: Taxation & Cross-Border Structuring

## FIN-0040 [建议]
判据: The response's CGT rationale for the Chilean SpA structure references Chile's right to tax gains on Chilean shares under the (now in-force) US-Chile treaty.
提示: CGT on exit is a fundamental economic factor.
出处: prbench:0855344d17abee65565d8b7d | 话题: Taxation & Cross-Border Structuring

## FIN-0041 [必须]
判据: The response's dividend repatriation model for the Dutch SPV scenario applies the correct WHT rates to the 2nd leg of the cash movement, 0-5% on NL-to-US, per NL-US treaty/LOB.
提示: This connects the tax analysis to the financial model.
出处: prbench:0855344d17abee65565d8b7d | 话题: Taxation & Cross-Border Structuring

## FIN-0042 [必须]
判据: The response discusses how to adjust the model to ensure comparability (e.g., firm size, FX, fiscal calendars, or revenue recognition variations).
提示: Address comparability across peers
出处: prbench:0d3f1d80bc8e8403e27be6e6 | 话题: Accounting & Financial Statement Analysis

## FIN-0043 [必须]
判据: The response includes normalization in the deferred revenue calculation (e.g., deferred revenue/total revenue).
提示: Explains the calculation method.
出处: prbench:0d3f1d80bc8e8403e27be6e6 | 话题: Accounting & Financial Statement Analysis

## FIN-0044 [必须]
判据: The response states that using pseudo-real-time prevents look-ahead bias.
提示: Recognize need for bias control
出处: prbench:0d3f1d80bc8e8403e27be6e6 | 话题: Accounting & Financial Statement Analysis

## FIN-0045 [必须]
判据: The response calculates the percent impact on NAV per share from a buyback of 1 million shares at 15 GEL each, with a starting NAV of 300 million GEL and 30 million shares.
提示: Ensures the response provides a verifiable, correct quantitative result for the scenario.
出处: prbench:0dc2e486e32fd1768e8be4e0 | 话题: Investment Strategy & Portfolio Design

## FIN-0046 [必须]
判据: The response states Georgia Capital's current dividend yield as a specific percentage.
提示: Essential for income return analysis
出处: prbench:0dc2e486e32fd1768e8be4e0 | 话题: Investment Strategy & Portfolio Design

## FIN-0047 [必须]
判据: The response states the specific percentage of NAV represented by Georgia Capital's largest business segment.
提示: Key concentration metric
出处: prbench:0dc2e486e32fd1768e8be4e0 | 话题: Investment Strategy & Portfolio Design

## FIN-0048 [必须]
判据: The response identifies at least five specific business segments of Georgia Capital PLC as of 2024: (1) healthcare/hospitals, (2) pharmacy retail, (3) property & casualty insurance, (4) education/schools, and (5) renewable energy/power generation.
提示: Essential for understanding company structure
出处: prbench:0dc2e486e32fd1768e8be4e0 | 话题: Investment Strategy & Portfolio Design

## FIN-0049 [必须]
判据: The response applies at least three specific valuation methods from the following list for private assets: (1) DCF with explicit local-currency WACC, (2) trading comparables with stated multiples, (3) precedent transactions with stated multiples, and (4) public market multiples with illiquidity/minority discounts.
提示: Establishes core valuation methodology
出处: prbench:0dc2e486e32fd1768e8be4e0 | 话题: Investment Strategy & Portfolio Design

## FIN-0050 [必须]
判据: The response evaluates board independence by specifically stating the percentage or number of independent directors on Georgia Capital's board.
提示: Quantifiable governance metric
出处: prbench:0dc2e486e32fd1768e8be4e0 | 话题: Investment Strategy & Portfolio Design

## FIN-0051 [必须]
判据: The response states Georgia Capital’s current dividend yield as a specific figure, for example, “The current dividend yield is 3.2%.”
提示: Key income return metric
出处: prbench:0dc2e486e32fd1768e8be4e0 | 话题: Investment Strategy & Portfolio Design

## FIN-0052 [负面]
判据: The response incorrectly treats the entirety of the capitalized software costs of $4.2m as fraudulent without noting that it may be GAAP-compliant but aggressive.
提示: Conflates aggressive accounting with fraud inappropriately.
出处: prbench:0ea5a8db2581823b03a3e766 | 话题: Accounting & Financial Statement Analysis

## FIN-0053 [必须]
判据: The response identifies that capitalizing software development costs (previously expensed) inflates assets on the balance sheet by the $4.2m capitalized amount.
提示: Understanding this accounting policy change is core to assessing earnings manipulation.
出处: prbench:0ea5a8db2581823b03a3e766 | 话题: Accounting & Financial Statement Analysis

## FIN-0054 [必须]
判据: The response adjusts the reported 16% EBITDA margin downward by adding back the $4.2m capitalized software costs as an expense, then recalculates the normalized margin (e.g., if revenue is implied, margin = (Original EBITDA - $4.2m) / Revenue).
提示: This adjustment is essential to determine how much of the margin improvement is accounting-driven versus operational.
出处: prbench:0ea5a8db2581823b03a3e766 | 话题: Accounting & Financial Statement Analysis

## FIN-0055 [必须]
判据: The response calculates Cash EBITDA or a similar adjusted metric by subtracting the capitalized software costs from reported EBITDA (e.g., Reported EBITDA - $4.2m = Cash EBITDA).
提示: Provides a normalized, cash-based profitability metric for comparison.
出处: prbench:0ea5a8db2581823b03a3e766 | 话题: Accounting & Financial Statement Analysis

## FIN-0056 [必须]
判据: The response calculates or estimates what the EBITDA margin would have been without the capitalization change (e.g., if still expensing all software costs, the margin would be closer to 12% or below, versus the reported 16%).
提示: Shows clear before/after comparison with transparent assumptions.
出处: prbench:0ea5a8db2581823b03a3e766 | 话题: Accounting & Financial Statement Analysis

## FIN-0057 [必须]
判据: The response checks whether the software capitalization meets GAAP/IFRS criteria (e.g., IAS 38 or ASC 985-20), specifically whether the costs relate to the application development stage versus preliminary/post-implementation stages that should be expensed.
提示: Validates whether the accounting policy change is appropriate or aggressive.
出处: prbench:0ea5a8db2581823b03a3e766 | 话题: Accounting & Financial Statement Analysis

## FIN-0058 [建议]
判据: The response calculates the cash conversion cycle using the formula: CCC = DSO + DIO - DPO (Days Sales Outstanding + Days Inventory Outstanding - Days Payable Outstanding).
提示: Comprehensive working capital analysis beyond just receivables.
出处: prbench:0ea5a8db2581823b03a3e766 | 话题: Accounting & Financial Statement Analysis

## FIN-0059 [建议]
判据: The response mentions that extended payment terms (78 vs 45 days DSO) reduce the time value of money on receivables by delaying cash collection by an additional 33 days.
提示: Sophisticated insight but not essential to core earnings quality assessment.
出处: prbench:0ea5a8db2581823b03a3e766 | 话题: Accounting & Financial Statement Analysis

## FIN-0060 [必须]
判据: The response calculates the percentage point gap between revenue growth (18%) and operating cash flow growth (3%) as 15 percentage points (18% - 3% = 15 pp).
提示: Quantifying this gap is fundamental to identifying the cash flow quality issue.
出处: prbench:0ea5a8db2581823b03a3e766 | 话题: Accounting & Financial Statement Analysis

## FIN-0061 [必须]
判据: The response calculates the additional cash tied up in receivables from the DSO increase: approximately (78 - 45) days × (Revenue / 365) to quantify the working capital drain in dollar terms.
提示: This calculation directly explains the OCF vs revenue growth discrepancy and is central to the analysis.
出处: prbench:0ea5a8db2581823b03a3e766 | 话题: Accounting & Financial Statement Analysis

## FIN-0062 [负面]
判据: The response states that forward contracts have 'zero cost'.
提示: This is a common and material misunderstanding. The cost of a forward is the difference between the forward rate and the eventual spot rate (the opportunity cost), not just the lack of a premium. Framing it as "zero cost" is professionally misleading.
出处: prbench:11438c888c22f9ebaa2896b1 | 话题: International Finance & FX Hedging

## FIN-0063 [必须]
判据: The response quantifies the hedgeable exposure as EUR cash inflows = EUR revenues minus EUR costs.
提示: identifying hedgeable exposure
出处: prbench:11438c888c22f9ebaa2896b1 | 话题: International Finance & FX Hedging

## FIN-0064 [建议]
判据: The response accurately frames the forward rate as a function of interest rate differentials (carry), not a bank's prediction of future spot rates.
提示: Misunderstanding this leads to the erroneous belief that forwards are "cheap" or "expensive" based on spot forecasts, rather than understanding they are priced by arbitrage.
出处: prbench:11438c888c22f9ebaa2896b1 | 话题: International Finance & FX Hedging

## FIN-0065 [必须]
判据: The response includes a recommendation to hedge only the net exposure (i.e., revenue minus EUR-denominated costs), not the gross €50M revenue.
提示: Hedging gross revenue when costs are in the same currency creates an over-hedged position, introducing significant and unnecessary currency risk.
出处: prbench:11438c888c22f9ebaa2896b1 | 话题: International Finance & FX Hedging

## FIN-0066 [必须]
判据: The response concludes that undiscounted cash flows are as follows: (8 years x 300,000 annual cash inflow) - (8 years x (25,000 annual maintenance cost)) = 2,200,000.
提示: This is an important intermediary step for calculating overall NPV.
出处: prbench:11aa99fc82c12646bc6893de | 话题: Corporate Finance

## FIN-0067 [必须]
判据: The response calculates the asset valuation as: machinery costs 1,500,000 + installation costs 100,000 + permit costs 25,000 = 1,625,000.
提示: Since asset value is a core ask, it is critical that the calculation be done correctly.
出处: prbench:11aa99fc82c12646bc6893de | 话题: Corporate Finance

## FIN-0068 [必须]
判据: The response recommends that the project should move forward due to the positive value of NPV.
提示: The prompt instructs the model to provide a recommendation should go forward so critical that information is given.
出处: prbench:11aa99fc82c12646bc6893de | 话题: Corporate Finance

## FIN-0069 [必须]
判据: The response determines that NPV should be calculated to assess the project's viability.
提示: Since the model is not overtly told how to assess the project, it should default to NPV based on that being the only viable method given the information given.
出处: prbench:11aa99fc82c12646bc6893de | 话题: Corporate Finance

## FIN-0070 [必须]
判据: The response concludes that discounted cash flows are as follows: (8 years x 300,000 annual cash inflow discounted at 1.05) - (8 years x (25,000 annual maintenance cost discounted at 1.05)) = 1,777,383.
提示: Essential calculation for determining viability of project.
出处: prbench:11aa99fc82c12646bc6893de | 话题: Corporate Finance

## FIN-0071 [必须]
判据: The response calculates the NPV of the project as: -1,675,000 initial cash outflow + 1,777,383 discounted cash inflows = 102,383.
提示: Output for decision making - critical to be accurate or can lead to wrong decision.
出处: prbench:11aa99fc82c12646bc6893de | 话题: Corporate Finance

## FIN-0072 [负面]
判据: The response states that GAAP allows for software conversion costs to be capitalized.
提示: Important information - user needs to be aware of what expenses are not capitalized.
出处: prbench:11aa99fc82c12646bc6893de | 话题: Corporate Finance

## FIN-0073 [必须]
判据: The response calculates the upfront costs as: machinery costs 1,500,000 + installation costs 100,000 + permit 25,000 + software conversion costs 25,000 + training 25,000 = 1,675,000.
提示: Proper calculation of upfront costs is key to further calculations.
出处: prbench:11aa99fc82c12646bc6893de | 话题: Corporate Finance

## FIN-0074 [负面]
判据: The response states that GAAP allows for training costs to be capitalized.
提示: Important information - user needs to be aware of what expenses are not capitalized.
出处: prbench:11aa99fc82c12646bc6893de | 话题: Corporate Finance

## FIN-0075 [必须]
判据: The response states that Brazilian tax residents are taxed on their worldwide income, meaning offshore entities or foreign exchange usage does not eliminate Brazilian tax liability.
提示: The prompt explicitly asks if offshore entities or moving jurisdictions helps. Clarifying that Brazilian residency means worldwide taxation is critical to prevent ineffective structuring attempts.
出处: prbench:1626ca89c89aeb6294ad11e3 | 话题: Taxation & Cross-Border Structuring

## FIN-0076 [负面]
判据: The response provides factually wrong information about Brazilian crypto taxation, such as stating an incorrect exemption threshold other than R$35,000, a wrong tax rate other than 15%, or false claims that crypto gains are not taxed.
提示: Getting the fundamental numbers wrong (threshold, rate) leads to non-compliance or overpayment. These are verifiable facts where error is inexcusable for a tax professional.
出处: prbench:1626ca89c89aeb6294ad11e3 | 话题: Taxation & Cross-Border Structuring

## FIN-0077 [必须]
判据: The response explicitly incorporates the full $1 billion investment envelope, detailing the timing and allocation across capex and opex in the financial model.
提示: To calculate.
出处: prbench:16bae3360d250818572be3aa | 话题: Corporate Finance

## FIN-0078 [必须]
判据: The response shows increasing revenue starting at $50 million in year 1 then growing to $900 million by year 10 in the financial model of Goldman Sachs' initiative.
提示: revenue growth
出处: prbench:16bae3360d250818572be3aa | 话题: Corporate Finance

## FIN-0079 [必须]
判据: The response uses a 10-12% discount rate on the Goldman Sachs' initiative's financial model (e.g., reflecting recessionary risk).
提示: discount rate
出处: prbench:16bae3360d250818572be3aa | 话题: Corporate Finance

## FIN-0080 [必须]
判据: The response uses between 2% and 4% growth in the terminal value calculation for the financial model of Goldman Sachs' initiative.
提示: terminal value
出处: prbench:16bae3360d250818572be3aa | 话题: Corporate Finance

## FIN-0081 [必须]
判据: The response specifies the required accounting standard for financial testing as either IFRS, Italian GAAP (OIC), or the Company's current accounting basis.
提示: Forces precise, auditable ratio computation.
出处: prbench:16cc2465447cfb10b8895343 | 话题: Corporate Finance

## FIN-0082 [必须]
判据: The response calculates the implied forward points or forward rate from the stated 4.5% annualised cost, using the formula: Forward Rate = Spot × (1 + Cost% × Years), or states implied forward points in pips given spot level and tenor (e.g., if spot 1.0850, 18-month forward ~1.0125, points = -725 pips).
提示: Forward points calculation demonstrates understanding of carry cost mechanics and enables comparison to market rates.
出处: prbench:16d740d6d4b95ab875055e5e | 话题: International Finance & FX Hedging

## FIN-0083 [必须]
判据: The response calculates zero-cost collar strike levels using option pricing methodology, stating either specific strikes with inputs (spot, tenor, vol, rates, delta) or a strike range with rationale (e.g., 25-delta put at 1.0350, 25-delta call at 1.1400 for spot 1.0850, 18-month, 8% vol, EUR/USD rates).
提示: Collar strike calculation.
出处: prbench:16d740d6d4b95ab875055e5e | 话题: International Finance & FX Hedging

## FIN-0084 [必须]
判据: The response calculates the natural offset from USD debt service, using the formula: $180m × (SOFR + 3.25%) = Annual Interest. (SOFR rate 180-day average 4.35%).
提示: Natural hedge quantification shows partial EUR revenue-USD debt offset reducing net hedging need.
出处: prbench:16d740d6d4b95ab875055e5e | 话题: International Finance & FX Hedging

## FIN-0085 [必须]
判据: The response quantifies French onshore hedging cost differential by calculating either: notional hedged onshore (40% × €450m = €180m); or incremental cost if onshore is more expensive (e.g., 20 bps × €180m = €360k).
提示: Onshore requirement creates structural constraint.
出处: prbench:16d740d6d4b95ab875055e5e | 话题: International Finance & FX Hedging

## FIN-0086 [必须]
判据: The response calculates the EUR-USD interest rate differential driving forward costs, in basis points or as a percentage (e.g., EUR 3.5%, USD 5.25%, differential 175 bps or 1.75%).
提示: Rate differential explains forward pricing under covered interest parity.
出处: prbench:16d740d6d4b95ab875055e5e | 话题: International Finance & FX Hedging

## FIN-0087 [必须]
判据: The response correctly identifies that hedges of the company's forecasted EUR revenues should be designated as cash flow hedges under ASC 815.
提示: Hedge classification determines P&L vs OCI treatment.
出处: prbench:16d740d6d4b95ab875055e5e | 话题: International Finance & FX Hedging

## FIN-0088 [必须]
判据: The response calculates the approximate NDF basis cost impact on the €270m NDF-hedged portion to arrive at a quantified cost over the 18-month tenor (e.g., 5 bps * €270m * 1.5 yrs ≈ €200k).
提示: NDF basis quantifies incremental cost of structural constraint affecting total hedging economics.
出处: prbench:16d740d6d4b95ab875055e5e | 话题: International Finance & FX Hedging

## FIN-0089 [必须]
判据: The response expresses the total P&L impact of carry on exposure over 18 months as a percentage of $2.2B in revenue (approximately 1.2-1.5%).
提示: P&L quantification demonstrates hedging cost to justify exploring alternative structures to CFO/Board.
出处: prbench:16d740d6d4b95ab875055e5e | 话题: International Finance & FX Hedging

## FIN-0090 [必须]
判据: The response quantifies the worst-case outcome for a zero-cost collar structure, calculating the maximum loss if EUR/USD falls below the floor strike (e.g., if the floor is 1.0350 and spot falls to 1.0200, the unhedged loss on €450m is $6.75m).
提示: Worst-case quantification enables board to assess maximum downside.
出处: prbench:16d740d6d4b95ab875055e5e | 话题: International Finance & FX Hedging

## FIN-0091 [必须]
判据: The response states that designating the forecast EUR revenue hedges as cash flow hedges under ASC 815 results in the effective portion of gains/losses being deferred in Other Comprehensive Income (OCI) until the revenue impacts earnings.
提示: Hedge classification determines P&L vs OCI treatment.
出处: prbench:16d740d6d4b95ab875055e5e | 话题: International Finance & FX Hedging

## FIN-0092 [必须]
判据: The response quantifies the total P&L impact of 4.5% carry on €450m exposure over 18 months, calculating: €450m × 4.5% × 1.5 years = €30.4m.
提示: P&L quantification demonstrates hedging cost to justify exploring alternative structures to CFO/Board.
出处: prbench:16d740d6d4b95ab875055e5e | 话题: International Finance & FX Hedging

## FIN-0093 [必须]
判据: The response specifies backtesting profit-per-trade >$25 after costs during VIX >25 (e.g., average captured spread minus execution costs, slippage, and fees must exceed $25 per round-trip, measured across 10,000+ historical trades).
提示: $25 net profit per trade during high volatility is challenging given increased slippage and cancellation rates; validates economic viability.
出处: prbench:16f7fbcc3c64278d9f5d5bff | 话题: Market Microstructure, Trading & Liquidity

## FIN-0094 [必须]
判据: The response correctly calculates the delta-equivalent hedge exposure.
提示: Delta-equivalent exposure determines actual hedge coverage.
出处: prbench:16fef4bc7d75cb9c36f8fd25 | 话题: Risk Management & Stress Testing

## FIN-0095 [必须]
判据: The response provides a clear explanation distinguishing hedge effectiveness from hedge efficiency as separate concepts.
提示: Conceptual understanding is fundamental to proper hedge analysis.
出处: prbench:16fef4bc7d75cb9c36f8fd25 | 话题: Risk Management & Stress Testing

## FIN-0096 [必须]
判据: The response correctly calculates post-hedge portfolio volatility.
提示: Post-hedge risk measurement validates hedge effectiveness.
出处: prbench:16fef4bc7d75cb9c36f8fd25 | 话题: Risk Management & Stress Testing

## FIN-0097 [必须]
判据: The response correctly calculates the portfolio's pre-hedge beta.
提示: Portfolio beta is essential for systematic risk measurement.
出处: prbench:16fef4bc7d75cb9c36f8fd25 | 话题: Risk Management & Stress Testing

## FIN-0098 [必须]
判据: The response notes that the GmbH remains a Constituent Entity within the German jurisdiction. E.g., it confirms the entity's status is determined by local corporate law for GloBE.
提示: This shows correct application of the entity definition rules.
出处: prbench:183cbb8570a066a73ee22d3a | 话题: Taxation & Cross-Border Structuring

## FIN-0099 [必须]
判据: The response identifies that GmbH post-election is a hybrid entity for GloBE purposes, e.g., describing the entity as a corporation locally but transparent for US tax.
提示: Correctly identifying the entity type is a foundational step.
出处: prbench:183cbb8570a066a73ee22d3a | 话题: Taxation & Cross-Border Structuring

## FIN-0100 [必须]
判据: The response confirms GloBE ETR calculations are strictly jurisdictional and not blended. E.g., States the Hungarian ETR is calculated separately from the German ETR.
提示: This demonstrates understanding of a core GloBE principle.
出处: prbench:183cbb8570a066a73ee22d3a | 话题: Taxation & Cross-Border Structuring

## FIN-0101 [负面]
判据: The response suggests that blending income from low-tax jurisdictions can improve the German ETR. E.g., states that Hungarian profits can be blended into the German calculation.
提示: This is a technically incorrect statement on jurisdictional blending.
出处: prbench:183cbb8570a066a73ee22d3a | 话题: Taxation & Cross-Border Structuring

## FIN-0102 [必须]
判据: The response explains a local QDMTT has primary taxing rights over the IIR or UTPR. E.g., it notes Germany's QDMTT would collect any top-up tax first.
提示: This assesses understanding of the GloBE collection hierarchy.
出处: prbench:183cbb8570a066a73ee22d3a | 话题: Taxation & Cross-Border Structuring

## FIN-0103 [负面]
判据: The response claims that local taxes paid in Germany are reallocated to the US jurisdiction. E.g., it includes a statement like 'German taxes are now allocated to the US for GloBE'.
提示: This fundamentally misinterprets the GloBE tax allocation mechanism.
出处: prbench:183cbb8570a066a73ee22d3a | 话题: Taxation & Cross-Border Structuring

## FIN-0104 [必须]
判据: The response explains that the CTB election allows German taxes to become directly creditable for US FTC purposes. E.g., it mentions that the election removes the need for deemed-paid credits.
提示: This shows a holistic view of US international tax interaction.
出处: prbench:183cbb8570a066a73ee22d3a | 话题: Taxation & Cross-Border Structuring

## FIN-0105 [必须]
判据: The response mentions the SBIE as a required adjustment to the GloBE income denominator. For example, it notes that the Substance-Based Income Exclusion will reduce GloBE profit.
提示: This tests knowledge of the top-up tax calculation mechanics.
出处: prbench:183cbb8570a066a73ee22d3a | 话题: Taxation & Cross-Border Structuring

## FIN-0106 [负面]
判据: Correctly states and applies the LCR, including that inflows are capped at 75% of outflows over 30 days.
提示: Foundational formula errors invalidate results and mislead readers.
出处: prbench:19a4b6c9436728d536efee7c | 话题: Risk Management & Stress Testing

## FIN-0107 [必须]
判据: The response calculates the unhedged portfolio monthly EBITDA variance as approximately 7.7 million USD.
提示: Tests the core quantitative output of the unhedged risk analysis.
出处: prbench:1a653e7b27db48e5dd504655 | 话题: International Finance & FX Hedging

## FIN-0108 [必须]
判据: The response calculates the estimated P&L impact on the hedged position under the stress scenario (USD/BRL 6.2, USD/CLP 1100) as approximately -0.7 million USD.
提示: Tests the quantitative outcome under stress.
出处: prbench:1a653e7b27db48e5dd504655 | 话题: International Finance & FX Hedging

## FIN-0109 [必须]
判据: Response must select the correct discount rate for calculating the forward rate, which is 0.0018.
提示: Important to get the correct final sterling receipt figure.
出处: prbench:1c334816b54b644ac08ef257 | 话题: International Finance & FX Hedging

## FIN-0110 [必须]
判据: Response correctly calculates the call option premium as £26,000.
提示: Important to get the correct final sterling receipt figure.
出处: prbench:1c334816b54b644ac08ef257 | 话题: International Finance & FX Hedging

## FIN-0111 [必须]
判据: Response correctly calculates the net sterling receipt figure from using a call option as approximately £958,848.
提示: This is the correct final figure for using a call option.
出处: prbench:1c334816b54b644ac08ef257 | 话题: International Finance & FX Hedging

## FIN-0112 [必须]
判据: Response must add the discount rate of 0.0018 to the spot rate of 1.3092 to get the correct forward rate of 1.3110.
提示: Important to get the correct final sterling receipt figure.
出处: prbench:1c334816b54b644ac08ef257 | 话题: International Finance & FX Hedging

## FIN-0113 [必须]
判据: Response must divide the dollar receipt of $1,300,000 by the correctly calculated forward rate of 1.3110 to get the net sterling receipt from the forward contract of approximately £991,609.
提示: This is the correct final figure for the forward contract.
出处: prbench:1c334816b54b644ac08ef257 | 话题: International Finance & FX Hedging

## FIN-0114 [必须]
判据: Response correctly identifies that a call option will be used instead of a put option.
提示: Important to get the correct final sterling receipt figure.
出处: prbench:1c334816b54b644ac08ef257 | 话题: International Finance & FX Hedging

## FIN-0115 [必须]
判据: Response must select the correct spot rate of 1.3092 when calculating the forward rate.
提示: Important to get the correct final sterling receipt figure.
出处: prbench:1c334816b54b644ac08ef257 | 话题: International Finance & FX Hedging

## FIN-0116 [必须]
判据: Response draws a direct comparison between the forward contract and the call option, stating that the forward contract provides a higher net receipt by approximately £32,761.
提示: Key comparison to include.
出处: prbench:1c334816b54b644ac08ef257 | 话题: International Finance & FX Hedging

## FIN-0117 [必须]
判据: Response calculates that growing from $45M to approximately $71M in revenue in 18 months would add roughly $21M in gross profit, assuming 80% SaaS gross margins.
提示: This demonstrates sophisticated understanding of the mathematical requirements for achieving profitability in SaaS businesses - connecting revenue growth to gross profit generation and identifying the specific operational leverage needed. This level of detailed breakeven analysis separates expert from novice responses.
出处: prbench:1c36ba8e82a27cf1b1f89498 | 话题: Corporate Finance

## FIN-0118 [必须]
判据: Response calculates that the target's current cash position ($12M) provides approximately 1.5 quarters of runway at the current $8M quarterly burn rate.
提示: This basic cash runway calculation demonstrates understanding of liquidity constraints and timing pressures that affect deal dynamics and creates urgency for the seller.
出处: prbench:1c36ba8e82a27cf1b1f89498 | 话题: Corporate Finance

## FIN-0119 [必须]
判据: Response calculates and states the Rule of 40 metric for the target company as approximately -35% (calculated as 35% growth rate minus 70% cash burn margin).
提示: The Rule of 40 calculation is a fundamental SaaS valuation metric that provides immediate insight into growth efficiency. This specific calculation demonstrates technical competency required for expert-level corporate finance analysis.
出处: prbench:1c36ba8e82a27cf1b1f89498 | 话题: Corporate Finance

## FIN-0120 [必须]
判据: Response calculates the specific additional debt service burden by stating that 60% debt on a $180M acquisition ($108M debt) at typical leveraged buyout rates (8-10%) adds approximately $8.6M to $10.8M in annual interest payments to a company already burning $32M annually.
提示: his calculation demonstrates understanding that acquisition debt service compounds the existing cash burn problem, making the total cash outflow over $40M annually. This specific quantitative analysis is essential for evaluating deal feasibility and demonstrates sophisticated LBO modeling capabilities.
出处: prbench:1c36ba8e82a27cf1b1f89498 | 话题: Corporate Finance

## FIN-0121 [负面]
判据: The response includes EPS-related decisions that prioritize short-term improvements over building underlying value (e.g., "avoiding investment may improve financial metrics and result in a higher stock price").
提示: Harms company long term.
出处: prbench:1e7d0eb6ef80446cd2893e81 | 话题: Corporate Finance

## FIN-0122 [必须]
判据: The response states that it is always value-destructive to invest in projects whose cost of capital exceeds their return.
提示: Supplemental information.
出处: prbench:1e7d0eb6ef80446cd2893e81 | 话题: Corporate Finance

## FIN-0123 [必须]
判据: The response recommends cutting investment in projects with ROIC lower than WACC.
提示: Pivot point.
出处: prbench:1e7d0eb6ef80446cd2893e81 | 话题: Corporate Finance

## FIN-0124 [必须]
判据: Response correctly states that the forward contract is approximately £56,626 cheaper than the call options.
提示: Key analysis to include.
出处: prbench:21b8611ca4c82a6a22369ed9 | 话题: International Finance & FX Hedging

## FIN-0125 [必须]
判据: Response correctly calculates the net sterling payment from the call options to be £3,248,539.
提示: This is the correct final figure for the call options.
出处: prbench:21b8611ca4c82a6a22369ed9 | 话题: International Finance & FX Hedging

## FIN-0126 [必须]
判据: The response calculates the option premium as £52,800.
提示: This is important for calculating the correct net sterling payment figure.
出处: prbench:21b8611ca4c82a6a22369ed9 | 话题: International Finance & FX Hedging

## FIN-0127 [必须]
判据: The response calculates the sterling payment from the forward contract as approximately £3,183,756 (£3,164,556 from converting $4.8m at 1.5166 $/£, plus £19,200 arrangement fee). Acceptable answers fall within ±£2,000 to allow for rounding.
提示: This is important for calculating the correct net sterling payment figure.
出处: prbench:21b8611ca4c82a6a22369ed9 | 话题: International Finance & FX Hedging

## FIN-0128 [必须]
判据: The response incorporates the arrangement fee of £19,200 in the forward settlement.
提示: This is the correct final figure for the forward contract.
出处: prbench:21b8611ca4c82a6a22369ed9 | 话题: International Finance & FX Hedging

## FIN-0129 [必须]
判据: The response uses the correct spot rate of 1.5150 - 1.5260 in the forward calculation.
提示: This is important for calculating the correct net sterling payment figure.
出处: prbench:21b8611ca4c82a6a22369ed9 | 话题: International Finance & FX Hedging

## FIN-0130 [必须]
判据: The response calculates the forward bid rate correctly as 1.5038 $/£ (using spot rate 1.5150 less four-month forward premium 0.0112).
提示: This is important for calculating the correct net sterling payment figure.
出处: prbench:21b8611ca4c82a6a22369ed9 | 话题: International Finance & FX Hedging

## FIN-0131 [必须]
判据: The response uses the correct forward premium of 0.0112 - 0.0094 in the calculation.
提示: This is important for calculating the correct net sterling payment figure.
出处: prbench:21b8611ca4c82a6a22369ed9 | 话题: International Finance & FX Hedging

## FIN-0132 [必须]
判据: The response selects the call option (not the put) as the relevant hedge.
提示: This is important for calculating the correct net sterling payment figure.
出处: prbench:21b8611ca4c82a6a22369ed9 | 话题: International Finance & FX Hedging

## FIN-0133 [建议]
判据: The response calculates the actual unhedged cost as approximately £3,210,000-£3,222,000 (due to pay $4.8m ÷ spot rate in 4 months 1.4895-1.4956).
提示: To show how much the user can save.
出处: prbench:21b8611ca4c82a6a22369ed9 | 话题: International Finance & FX Hedging

## FIN-0134 [必须]
判据: The response must explain Section 1045 rollover mechanics, specifically the 60-day reinvestment window.
提示: Contextual advice.
出处: prbench:2389ab1ca1888cf9e9641281 | 话题: Taxation & Cross-Border Structuring

## FIN-0135 [必须]
判据: The response explicitly says that the federal 1202 gain exclusion applies only to gains on qualifying QSBS held no less than 5 years (counted from original issuance to sale).
提示: Foundation of the prompt.
出处: prbench:2389ab1ca1888cf9e9641281 | 话题: Taxation & Cross-Border Structuring

## FIN-0136 [必须]
判据: The response must clarify that wash-sale disallowed prices are added to the basis of new shares.
提示: Realistic example.
出处: prbench:2389ab1ca1888cf9e9641281 | 话题: Taxation & Cross-Border Structuring

## FIN-0137 [必须]
判据: The response states that, if exercised, the put options provide a higher receipt of approximately £22,929 compared to the forward contract.
提示: Key analysis to include.
出处: prbench:24b1cad66aa38228ce116699 | 话题: International Finance & FX Hedging

## FIN-0138 [必须]
判据: The response adds the discount rate of 0.0085 to the spot rate of 1.6385 to get the correct forward rate of 1.6470.
提示: Important to get the correct final sterling receipt figure.
出处: prbench:24b1cad66aa38228ce116699 | 话题: International Finance & FX Hedging

## FIN-0139 [必须]
判据: The response calculates the forward contract fee as £18,200.
提示: Important to get the correct final sterling receipt figure.
出处: prbench:24b1cad66aa38228ce116699 | 话题: International Finance & FX Hedging

## FIN-0140 [必须]
判据: The response selects put options over call options.
提示: Important to get the correct final sterling receipt figure.
出处: prbench:24b1cad66aa38228ce116699 | 话题: International Finance & FX Hedging

## FIN-0141 [必须]
判据: The response divides the dollar receipt of $5,200,000 by the correctly calculated forward rate of 1.6470 to get the sterling receipt from the forward contract of approximately £3,157,256.
提示: Key to get the correct final sterling receipt figure.
出处: prbench:24b1cad66aa38228ce116699 | 话题: International Finance & FX Hedging

## FIN-0142 [必须]
判据: The response selects the correct discount rate for calculating the forward rate, being 0.0085.
提示: Important to get the correct final sterling receipt figure.
出处: prbench:24b1cad66aa38228ce116699 | 话题: International Finance & FX Hedging

## FIN-0143 [必须]
判据: The response calculates the cost of the put options to be £39,000.
提示: Important to get the correct final sterling receipt figure.
出处: prbench:24b1cad66aa38228ce116699 | 话题: International Finance & FX Hedging

## FIN-0144 [必须]
判据: The response deducts the £18,200 fee from the sterling receipt from the forward contract of £3,157,256, to get the correct final net sterling receipt of £3,139,056.
提示: This is the correct final figure for the forward contract.
出处: prbench:24b1cad66aa38228ce116699 | 话题: International Finance & FX Hedging

## FIN-0145 [必须]
判据: The response calculates the net sterling receipt from exercising the put options to be approximately £3,161,985 (+/- £10,000).
提示: The correct figure for the put options.
出处: prbench:24b1cad66aa38228ce116699 | 话题: International Finance & FX Hedging

## FIN-0146 [必须]
判据: The response selects the correct spot rate of 1.6385 when calculating the forward rate.
提示: Important to get the correct final sterling receipt figure.
出处: prbench:24b1cad66aa38228ce116699 | 话题: International Finance & FX Hedging

## FIN-0147 [负面]
判据: Provides directly contradictory specifications for the same metric or allocation within different sections of the response.
提示: tests for internal inconsistencies that make the proposal ambiguous
出处: prbench:267f693527d8ffd5fc4b6b1c | 话题: Investment Strategy & Portfolio Design

## FIN-0148 [必须]
判据: States the effective portfolio duration as a single number in years.
提示: Confirms proper duration management aligned with rate outlook.
出处: prbench:267f693527d8ffd5fc4b6b1c | 话题: Investment Strategy & Portfolio Design

## FIN-0149 [负面]
判据: States allocation percentages that mathematically sum to more than 100% or less than 100% of the total portfolio.
提示: Presents a fundamental mathematical error that undermines the entire allocation proposal's credibility and implementability.
出处: prbench:267f693527d8ffd5fc4b6b1c | 话题: Investment Strategy & Portfolio Design

## FIN-0150 [必须]
判据: The response calculates adjusted EBIT by expensing the £8m capitalised factory modernisation costs under IAS 16.
提示: Fundamental accounting correction affecting all subsequent covenant calculations.
出处: prbench:2867c946e949e41c36d5f3ae | 话题: Corporate Finance

## FIN-0151 [必须]
判据: The response concludes that the £80m asset disposal alone does not achieve the 1.5x ICR covenant threshold across all scenarios.
提示: Tests realistic assessment versus over-optimistic single-option thinking.
出处: prbench:2867c946e949e41c36d5f3ae | 话题: Corporate Finance

## FIN-0152 [必须]
判据: The response calculates the probability-weighted likelihood of covenant breach incorporating all three scenario probabilities.
提示: Tests statistical integration capability beyond discrete scenario analysis.
出处: prbench:2867c946e949e41c36d5f3ae | 话题: Corporate Finance

## FIN-0153 [必须]
判据: The response calculates quarter-by-quarter covenant compliance rather than treating the 18-month period as a single annual test.
提示: Tests understanding of quarterly testing mechanics versus annual averages.
出处: prbench:2867c946e949e41c36d5f3ae | 话题: Corporate Finance

## FIN-0154 [必须]
判据: The response calculates variable interest expense changes by applying SONIA increases only to the £100m variable rate tranche.
提示: Tests technical understanding of interest rate sensitivity mechanics.
出处: prbench:2867c946e949e41c36d5f3ae | 话题: Corporate Finance

## FIN-0155 [必须]
判据: The response correctly identifies the gift as a Potentially Exempt Transfer (PET).
提示: A fundamental part of the IHT analysis and a core requirement of the prompt.
出处: prbench:2afa19b8219898c818c3e644 | 话题: Taxation & Cross-Border Structuring

## FIN-0156 [必须]
判据: The response correctly explains that a formal loan remains an asset within the parent's estate for inheritance tax (IHT) purposes (e.g., a loan remains in the estate).
提示: Correctly identifying the IHT treatment of the loan is a core part of the required comparison.
出处: prbench:2afa19b8219898c818c3e644 | 话题: Taxation & Cross-Border Structuring

## FIN-0157 [必须]
判据: The response states a gift falls outside the IHT estate if the giver lives for 7 years after making it (e.g., survive 7 years and the gift is outside the estate; the 7-year rule applies to PETs).
提示: A fundamental part of the IHT analysis.
出处: prbench:2afa19b8219898c818c3e644 | 话题: Taxation & Cross-Border Structuring

## FIN-0158 [建议]
判据: The response states that if the giver dies between years 3-7 after a gift, the tax on the part above the allowance can decrease.
提示: A correct but secondary detail of the IHT rules for PETs.
出处: prbench:2afa19b8219898c818c3e644 | 话题: Taxation & Cross-Border Structuring

## FIN-0159 [必须]
判据: The response states the effects of convexity or extension risk on the NAV estimate (e.g., a back-of-the-envelope calculation ignores convexity that lessens the loss).
提示: By ignore the convexity can lead to significant underestimation of the risks in special for callable bonds in stressful markets.
出处: prbench:2b2486c2a9eca2381889f118 | 话题: Risk Management & Stress Testing

## FIN-0160 [必须]
判据: The response calculates the DV01 or sensitivity per basis point for the portfolio (e.g., DV01 of $200k/bp).
提示: DV01 is a standard risk measure that facilitates precise hedging and risk assessment.
出处: prbench:2b2486c2a9eca2381889f118 | 话题: Risk Management & Stress Testing

## FIN-0161 [必须]
判据: The response defines modified duration as the percentage price change for a small, parallel change in yield.
提示: Establishes the sensitivity concept used for hedging.
出处: prbench:2b61a610a4ac61d8c9e9a238 | 话题: Derivatives & Structured Products

## FIN-0162 [必须]
判据: The response explains portfolio modified duration as a market-value-weighted combination of the individual bonds’ modified durations.
提示: Gives the correct aggregation method.
出处: prbench:2b61a610a4ac61d8c9e9a238 | 话题: Derivatives & Structured Products

## FIN-0163 [必须]
判据: The response defines DV01 (PV01/BPV) as the dollar change in portfolio value for a 1 basis point (0.01%) change in yield.
提示: Converts percentage sensitivity into hedgeable dollar risk.
出处: prbench:2b61a610a4ac61d8c9e9a238 | 话题: Derivatives & Structured Products

## FIN-0164 [必须]
判据: The response states that hedge sizing matches the magnitude of the futures’ total DV01 to the portfolio’s DV01.
提示: Captures the core hedge ratio concept.
出处: prbench:2b61a610a4ac61d8c9e9a238 | 话题: Derivatives & Structured Products

## FIN-0165 [必须]
判据: Defines the Notional Amount of a Futures Contract as the total value of the underlying asset that the contract controls.
提示: Another key definition for the case.
出处: prbench:2b61a610a4ac61d8c9e9a238 | 话题: Derivatives & Structured Products

## FIN-0166 [必须]
判据: The response states that the hedge position must be in the opposite direction to the portfolio’s rate exposure (long duration → short futures; short duration → long futures).
提示: Prevents hedges that unintentionally add risk.
出处: prbench:2b61a610a4ac61d8c9e9a238 | 话题: Derivatives & Structured Products

## FIN-0167 [必须]
判据: The response states that bond prices move in the opposite direction to yield changes.
提示: Prevents sign errors when interpreting duration.
出处: prbench:2b61a610a4ac61d8c9e9a238 | 话题: Derivatives & Structured Products

## FIN-0168 [建议]
判据: The response states that convexity is a risk measure that accounts for the fact that a bond's price-yield relationship is not linear.
提示: Important to complete the risk management subject.
出处: prbench:2b61a610a4ac61d8c9e9a238 | 话题: Derivatives & Structured Products

## FIN-0169 [建议]
判据: The response states that when hedging non-Treasury bonds, a yield-beta adjustment may be used based on historical co-movement with the CTD.
提示: Reduces basis risk between credit and Treasury rates.
出处: prbench:2b61a610a4ac61d8c9e9a238 | 话题: Derivatives & Structured Products

## FIN-0170 [负面]
判据: The response treats factor exposures as independent variables, ignoring that value tilt and low-vol factor are typically correlated characteristics in portfolios.
提示: Misunderstands the relationship between factor exposures.
出处: prbench:2b6ebd8a7aae367301508372 | 话题: Investment Strategy & Portfolio Design

## FIN-0171 [必须]
判据: The response evaluates whether the original underweight conviction was based on sound fundamental analysis supported by the valuation model showing 22x fair value.
提示: Assesses whether conviction remains justified.
出处: prbench:2b6ebd8a7aae367301508372 | 话题: Investment Strategy & Portfolio Design

## FIN-0172 [必须]
判据: The response calculates the valuation premium as 27% by computing (28/22) - 1 when comparing the 28x forward P/E market price to the 22x fair value model estimate.
提示: Quantifies the valuation risk embedded in the decision.
出处: prbench:2b6ebd8a7aae367301508372 | 话题: Investment Strategy & Portfolio Design

## FIN-0173 [必须]
判据: The response reconciles the $70m figure with portfolio math, for example, by explaining it represents current market value at elevated prices when closing half the gap from 12% to 20% weight (e.g., calculating (28% - 12%) × 50% × $500m = $40m notional × 1.75 price premium = $70m).
提示: Reconciling the stated $70m investment with portfolio math is essential to understanding the trade-off.
出处: prbench:2b6ebd8a7aae367301508372 | 话题: Investment Strategy & Portfolio Design

## FIN-0174 [必须]
判据: The response calculates the marginal contribution to risk (MCTR) of increasing tech exposure from 12% to 20%, showing the impact on portfolio volatility (e.g., MCTR = β_tech × σ_portfolio × Δweight).
提示: Quantifies how closing the gap affects overall risk metrics.
出处: prbench:2b6ebd8a7aae367301508372 | 话题: Investment Strategy & Portfolio Design

## FIN-0175 [必须]
判据: The response quantifies the factor exposure drift from 0.4 value tilt to -0.2 as a 0.6 standard deviation shift in portfolio style.
提示: Quantifying style drift is central to the mandate risk assessment.
出处: prbench:2b6ebd8a7aae367301508372 | 话题: Investment Strategy & Portfolio Design

## FIN-0176 [必须]
判据: The response explains that standard tracking error formulas (TE = √[(w_portfolio - w_benchmark)² × σ² × (1-ρ²)]) fail when buying stocks specifically because they're expensive, since correlation and volatility inputs become endogenous to the purchase decision itself.
提示: This paradox is the core technical question in the prompt.
出处: prbench:2b6ebd8a7aae367301508372 | 话题: Investment Strategy & Portfolio Design

## FIN-0177 [负面]
判据: The response includes suggestions that informal valuation methods or "rules of thumb" are sufficient for determining business worth.
提示: Informal valuation approaches are inadequate for founder disputes and can lead to significant financial exposure.
出处: prbench:2c12a61d8826e31dabc96499 | 话题: Corporate Finance

## FIN-0178 [必须]
判据: The response identifies at least two specific business valuation methodologies appropriate for a tech start-up with recent founder conflict.
提示: Accurate valuation is fundamental to any business sale decision. Models often struggle with selecting appropriate methodologies for distressed or conflict situations, frequently defaulting to generic approaches without considering the specific context of founder disputes and their impact on valuation multiples.
出处: prbench:2c12a61d8826e31dabc96499 | 话题: Corporate Finance

## FIN-0179 [必须]
判据: The response states the standalone EBITDA change due to restatement, "such as EBITDA declined by 13m Euros (161m Euros - 148m Euros).".
提示: Verifies grasp of how the revenue adjustment flows through to EBITDA
出处: prbench:2d2bd6c735f5c7ffb946f518 | 话题: Accounting & Financial Statement Analysis

## FIN-0180 [必须]
判据: Determine IAS 8 classification (prior-period error vs change in accounting policy).
提示: Ensures the respondent distinguishes between an accounting-policy change and an error correction, as required by IAS 8.
出处: prbench:2d2bd6c735f5c7ffb946f518 | 话题: Accounting & Financial Statement Analysis

## FIN-0181 [必须]
判据: The response rebalances using each risk bucket's share of total risk.
提示: Checks for trading discipline.
出处: prbench:2fc93575d4f6df8beb61fc77 | 话题: Investment Strategy & Portfolio Design

## FIN-0182 [必须]
判据: The response either scales the long-term pool's active risk or the weight of the long-term pool, not both with the same stress signal.
提示: Checks if the response prevents double shrinking of risk in stress times.
出处: prbench:2fc93575d4f6df8beb61fc77 | 话题: Investment Strategy & Portfolio Design

## FIN-0183 [必须]
判据: The response states the risk model includes all of the following: interest rate curve; credit quality/spreads; convexity; foreign exchange risk.
提示: Checks if the response manage risk on a single dimension only.
出处: prbench:2fc93575d4f6df8beb61fc77 | 话题: Investment Strategy & Portfolio Design

## FIN-0184 [必须]
判据: The response correctly states the purpose of tracking error: it measures volatility of active returns vs. the benchmark.
提示: checks if the response knows exactly what tracking error measures.
出处: prbench:2fc93575d4f6df8beb61fc77 | 话题: Investment Strategy & Portfolio Design

## FIN-0185 [负面]
判据: Provides an incorrect or overly simplistic calculation for the equity cure (e.g., suggesting a debt paydown of 4.0x the shortfall instead of an equity infusion equal to the shortfall).
提示: Providing incorrect core financial mechanics is dangerously misleading and could directly lead to a failed strategy and covenant breach.
出处: prbench:343bf0c67c29490c7e886961 | 话题: Corporate Finance

## FIN-0186 [必须]
判据: Includes instructions to calculate covenant compliance using the precise definitions of 'EBITDA' and 'Net Debt' from the credit agreement, not GAAP/IFRS.
提示: The entire scenario hinges on this calculation. An expert response must immediately focus on the contractual definitions, which always contain material addbacks and exclusions.
出处: prbench:343bf0c67c29490c7e886961 | 话题: Corporate Finance

## FIN-0187 [必须]
判据: Includes a specific, correct formula for calculating the required equity cure amount (e.g., Shortfall = Required EBITDA - Actual EBITDA; Cure Amount = Shortfall).
提示: Misstating this common but precise mechanic would lead to a severely under or over-sized cure, potentially jeopardizing the entire strategy.
出处: prbench:343bf0c67c29490c7e886961 | 话题: Corporate Finance

## FIN-0188 [负面]
判据: The response includes a performance improvement claim such as “eliminate all implementation shortfall” or “reduce costs to zero,” without acknowledging market impact limitations or the inherent costs of executing institutional-sized orders.
提示: Penalises unrealistic expectations that demonstrate poor understanding of market microstructure constraints. Self-contained focus on performance projection realism.
出处: prbench:358d2c96ff16bfdfcfb477a5 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0189 [必须]
判据: The response specifies benchmarking against size-adjusted VWAP rather than standard VWAP for mid-cap orders.
提示: Tests understanding of benchmark-relative performance improvement. Self-contained focus on VWAP underperformance mitigation.
出处: prbench:358d2c96ff16bfdfcfb477a5 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0190 [必须]
判据: The analysis states that a Takeover Offer requires 90% acceptance of the shares to which the offer relates to guarantee the compulsory squeeze-out of remaining minority shareholders.
提示: The 90% squeeze-out threshold is a fundamental rule governing UK Takeover Offers.
出处: prbench:3638968f6709c40ec9724b0c | 话题: Corporate Finance

## FIN-0191 [必须]
判据: The response states the dual approval threshold for a Scheme of Arrangement: 75% in value and a majority in number (the headcount test) of those shareholders voting in each relevant class.
提示: These dual thresholds are the specific legal requirements for a Scheme of Arrangement under the Companies Act.
出处: prbench:3638968f6709c40ec9724b0c | 话题: Corporate Finance

## FIN-0192 [建议]
判据: The response defines a Takeover Offer as a direct offer made by the bidder to the target company's shareholders.
提示: A correct definition is an important component of the analysis.
出处: prbench:3638968f6709c40ec9724b0c | 话题: Corporate Finance

## FIN-0193 [必须]
判据: The analysis justifies the recommendation by explaining that the 75% threshold for a Scheme offers higher execution certainty for achieving 100% control than the 90% threshold for an Offer.
提示: The core commercial and legal rationale for preferring a Scheme in a friendly transaction.
出处: prbench:3638968f6709c40ec9724b0c | 话题: Corporate Finance

## FIN-0194 [必须]
判据: The response explains that a Scheme of Arrangement, once sanctioned by the court, binds all shareholders and automatically delivers 100% control.
提示: The ability to bind all shareholders is the key mechanical advantage of a Scheme for achieving 100% ownership.
出处: prbench:3638968f6709c40ec9724b0c | 话题: Corporate Finance

## FIN-0195 [建议]
判据: The response identifies that a Takeover Offer can become unconditional as to acceptances when they exceed 50%, delivering control to the bidder.
提示: The >50% threshold for gaining control is a key mechanical feature of a UK Takeover Offer.
出处: prbench:3638968f6709c40ec9724b0c | 话题: Corporate Finance

## FIN-0196 [建议]
判据: The response defines a Scheme of Arrangement as a UK court-supervised process proposed by the target company under the Companies Act 2006.
提示: A correct definition is a foundational component of the analysis.
出处: prbench:3638968f6709c40ec9724b0c | 话题: Corporate Finance

## FIN-0197 [必须]
判据: The response explains the differential impact of voter apathy, noting that non-participating shareholders count against the 90% absolute target of an Offer but not against the 75% threshold of voted shares in a Scheme.
提示: How shareholder behaviour affects the probability of success for each structure.
出处: prbench:3638968f6709c40ec9724b0c | 话题: Corporate Finance

## FIN-0198 [必须]
判据: The response states that a salary of £2,700 suggests a yearly salary of about £32,400.
提示: This sets the basis for the loan repayment and savings calculations
出处: prbench:3676117fb45c0b48ce245348 | 话题: Wealth Management, Financial Planning & Advice

## FIN-0199 [必须]
判据: The response determines that the student loan is Plan 2 since the user is currently in a graduate trainee job (e.g., Plan 2 applies to borrowers who started uni after April 2012, including graduate trainees).
提示: This sets the basis for the right repayment amount for the loan
出处: prbench:3676117fb45c0b48ce245348 | 话题: Wealth Management, Financial Planning & Advice

## FIN-0200 [必须]
判据: The response identifies fleeting liquidity as a market microstructure problem caused by HFT/algo behavior, e.g., ghost liquidity from HFTs or quotes pulled when an interest rate is detected.
提示: Understanding the root cause of fleeting liquidity demonstrates sophisticated market microstructure knowledge.
出处: prbench:36b4c80c513d52464f714b88 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0201 [必须]
判据: The response correctly explains that 15% of 18mm actual volume equals approximately 2.7mm shares/day, e.g., it demonstrates quantitative understanding of the participation rate problem.
提示: This specific calculation separates experts from generalists.
出处: prbench:36b4c80c513d52464f714b88 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0202 [必须]
判据: The response identifies that EBITDA margins will increase because rent expense is replaced by depreciation.
提示: Key ratio manipulation that affects valuation multiples and performance assessment.
出处: prbench:36efe9e547d3914c28a636c9 | 话题: Accounting & Financial Statement Analysis

## FIN-0203 [必须]
判据: The response states that performance/usage-based variable lease payments (e.g., % of sales, units used) are excluded from initial measurement.
提示: Technical complexity that significantly affects liability measurement.
出处: prbench:36efe9e547d3914c28a636c9 | 话题: Accounting & Financial Statement Analysis

## FIN-0204 [必须]
判据: The response explains that straight-line rent expense is replaced by depreciation expense on the right-of-use asset.
提示: Core component of income statement remapping under IFRS 16.
出处: prbench:36efe9e547d3914c28a636c9 | 话题: Accounting & Financial Statement Analysis

## FIN-0205 [必须]
判据: The response identifies that net debt to EBITDA ratios will worsen because lease liabilities increase the numerator more than the annual rent increases the denominator.
提示: Critical leverage metric impact with quantified directional explanation.
出处: prbench:36efe9e547d3914c28a636c9 | 话题: Accounting & Financial Statement Analysis

## FIN-0206 [必须]
判据: The response explains how IAS 36 interacts with onerous contract provisions (IAS 37) for loss-making stores where the right-of-use asset may require immediate impairment.
提示: Sector-specific complexity for retailers with unprofitable stores.
出处: prbench:36efe9e547d3914c28a636c9 | 话题: Accounting & Financial Statement Analysis

## FIN-0207 [必须]
判据: The response explains that return on assets will decline because the right-of-use asset increases the denominator more than any improvement in net income in the numerator.
提示: Important capital efficiency metric demonstrating reduced apparent asset productivity.
出处: prbench:36efe9e547d3914c28a636c9 | 话题: Accounting & Financial Statement Analysis

## FIN-0208 [必须]
判据: The response explains that lease liabilities generate interest expense calculated using the discount rate applied at lease commencement.
提示: Second core component of income statement remapping that affects financing costs.
出处: prbench:36efe9e547d3914c28a636c9 | 话题: Accounting & Financial Statement Analysis

## FIN-0209 [负面]
判据: The response assumes that full retrospective transition is the standard method rather than the more commonly used modified retrospective approach.
提示: Technical error that demonstrates lack of detailed IFRS 16 implementation knowledge.
出处: prbench:36efe9e547d3914c28a636c9 | 话题: Accounting & Financial Statement Analysis

## FIN-0210 [必须]
判据: The response explains that IFRS 16 requires recognition of right-of-use assets on the balance sheet for previously off-balance sheet operating leases.
提示: This is the fundamental change under IFRS 16 and forms the basis for all other impacts.
出处: prbench:36efe9e547d3914c28a636c9 | 话题: Accounting & Financial Statement Analysis

## FIN-0211 [必须]
判据: The response explains that IFRS 16 requires recognition of lease liabilities representing the present value of future lease payments.
提示: The corresponding liability recognition is equally fundamental to understanding balance sheet changes.
出处: prbench:36efe9e547d3914c28a636c9 | 话题: Accounting & Financial Statement Analysis

## FIN-0212 [必须]
判据: The response explains that principal repayments on lease liabilities are classified as financing cash outflows rather than operating cash outflows.
提示: Material presentational change that artificially improves operating cash flow metrics.
出处: prbench:36efe9e547d3914c28a636c9 | 话题: Accounting & Financial Statement Analysis

## FIN-0213 [必须]
判据: The response states that variable lease payments linked to an index or rate (e.g., CPI) are included in the initial measurement of the lease liability/ROU asset.
提示: Technical complexity that significantly affects liability measurement.
出处: prbench:36efe9e547d3914c28a636c9 | 话题: Accounting & Financial Statement Analysis

## FIN-0214 [必须]
判据: The response states that OECD guidance treats control over DEMPE decisions, not mere location of personnel, as the determinant of IP return allocation.
提示: reason for core path A selection
出处: prbench:37c01defe80e632ed784bb68 | 话题: Taxation & Cross-Border Structuring

## FIN-0215 [必须]
判据: The response defends its position to not relocate DEMPE to Ireland by demonstrating that the Irish entity carries adequate economic substance for the return it earns (i.e., limited-risk IP ownership with outsourced DEMPE back to the UK under arm’s-length pricing).
提示: Defence for option A
出处: prbench:37c01defe80e632ed784bb68 | 话题: Taxation & Cross-Border Structuring

## FIN-0216 [必须]
判据: The response concludes that relocation under Path B yields negligible rate advantage after QDMTT + GILTI.
提示: reason for selecting path A
出处: prbench:37c01defe80e632ed784bb68 | 话题: Taxation & Cross-Border Structuring

## FIN-0217 [必须]
判据: The response identifies US dollar weakness as a transmission mechanism amplifying gold demand when the Fed cuts rates.
提示: USD channel is second-order effect of rate cuts on dollar-denominated gold prices.
出处: prbench:382f1841ab8c8c896d1ea942 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0218 [必须]
判据: The response explains that lower interest rates reduce the opportunity cost of holding non-yielding gold.
提示: Opportunity cost concept explains why rate cuts make gold relatively more attractive.
出处: prbench:382f1841ab8c8c896d1ea942 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0219 [必须]
判据: The response states the current or recent 10-year TIPS yield level with a specific value (e.g., currently 1.8% or recently declined from 2.1% to 1.5%).
提示: Current real yield level provides actionable baseline for assessing entry point.
出处: prbench:382f1841ab8c8c896d1ea942 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0220 [必须]
判据: The response identifies real yields as the primary transmission mechanism linking Fed rate cuts to gold demand.
提示: Real yields are foundational concept for understanding rate cuts impact on non-yielding assets.
出处: prbench:382f1841ab8c8c896d1ea942 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0221 [必须]
判据: The response states that the UK does not tax funds received as part of an inheritance.
提示: Tax obligations in the UK.
出处: prbench:3911aa828f48cd0981bc286e | 话题: Taxation & Cross-Border Structuring

## FIN-0222 [必须]
判据: The response normalizes EBIT by adjusting for acquisition‑related effects (e.g., purchase price allocation, one‑time integration costs).
提示: Required by the prompt.
出处: prbench:3ae660eb687032b38a51a9d2 | 话题: Accounting & Financial Statement Analysis

## FIN-0223 [必须]
判据: The response evaluates deferred tax timing effects by identifying at least one temporary difference (e.g., accelerated depreciation vs. tax depreciation).
提示: Explicitly asked by the user.
出处: prbench:3ae660eb687032b38a51a9d2 | 话题: Accounting & Financial Statement Analysis

## FIN-0224 [必须]
判据: The response quantifies the difference between the effective tax rate and the statutory tax rate in percentage points to isolate tax effects.
提示: To correctly calculate.
出处: prbench:3ae660eb687032b38a51a9d2 | 话题: Accounting & Financial Statement Analysis

## FIN-0225 [必须]
判据: The response normalizes EBIT by adjusting for depreciation policy changes (e.g., straight‑line vs. accelerated).
提示: Required by the prompt.
出处: prbench:3ae660eb687032b38a51a9d2 | 话题: Accounting & Financial Statement Analysis

## FIN-0226 [必须]
判据: The response concludes that the firm’s post‑acquisition performance, under adjusted assumptions, falls short of an 8% cost of capital.
提示: Explicitly asked by the user.
出处: prbench:3ae660eb687032b38a51a9d2 | 话题: Accounting & Financial Statement Analysis

## FIN-0227 [必须]
判据: The response explicitly states that under IFRS (IAS 16) and US GAAP (ASC 360), depreciation is recognized in profit or loss as an operating expense included in EBIT, regardless of whether expenses are presented by function or nature.
提示: Analytical precision.
出处: prbench:3ae660eb687032b38a51a9d2 | 话题: Accounting & Financial Statement Analysis

## FIN-0228 [必须]
判据: The response estimates adjusted ROIC by calculating Adjusted EBIT ÷ Invested Capital.
提示: Required by the prompt.
出处: prbench:3ae660eb687032b38a51a9d2 | 话题: Accounting & Financial Statement Analysis

## FIN-0229 [必须]
判据: The response computes the effective tax rate as total income tax expense ÷ pre‑tax income.
提示: Demands P&L integration.
出处: prbench:3ae660eb687032b38a51a9d2 | 话题: Accounting & Financial Statement Analysis

## FIN-0230 [必须]
判据: The response identifies and quantifies at least two working capital drivers (e.g., timing of customer collections, level of raw materials, WIP, and finished goods held) that together explain at least 90% of the change in operating cash flow.
提示: Requires causal reasoning.
出处: prbench:3ae660eb687032b38a51a9d2 | 话题: Accounting & Financial Statement Analysis

## FIN-0231 [必须]
判据: The response identifies that the acquisition of the competitor changed ROA and ROE the most.
提示: Required by the prompt.
出处: prbench:3ae660eb687032b38a51a9d2 | 话题: Accounting & Financial Statement Analysis

## FIN-0232 [必须]
判据: The response reconciles computed FCF using both the indirect and direct methods within 1%.
提示: Rare insight.
出处: prbench:3ae660eb687032b38a51a9d2 | 话题: Accounting & Financial Statement Analysis

## FIN-0233 [必须]
判据: The answer adjusts EBITDA for non-recurring restructuring costs and restates margins accordingly, showing both pre- and post-adjustment percentages.
提示: Accuracy recalculation.
出处: prbench:3ae660eb687032b38a51a9d2 | 话题: Accounting & Financial Statement Analysis

## FIN-0234 [必须]
判据: The response estimates adjusted ROA by calculating Adjusted EBIT ÷ Average Total Assets.
提示: Required by the prompt.
出处: prbench:3ae660eb687032b38a51a9d2 | 话题: Accounting & Financial Statement Analysis

## FIN-0235 [必须]
判据: The response correctly states that as a new US resident, the user is required to report their worldwide income to the Internal Revenue Service (IRS).
提示: States core US tax obligation.
出处: prbench:3c8219e988f4caa886b1201e | 话题: Taxation & Cross-Border Structuring

## FIN-0236 [必须]
判据: The response correctly states that the user remains obligated to pay UK tax on their UK-source rental income.
提示: States core UK tax obligation.
出处: prbench:3c8219e988f4caa886b1201e | 话题: Taxation & Cross-Border Structuring

## FIN-0237 [必须]
判据: The response mentions the user can deduct allowable expenses (e.g., letting agent fees, repairs) from their rental income for UK tax purposes.
提示: Tests practical tax knowledge.
出处: prbench:3c8219e988f4caa886b1201e | 话题: Taxation & Cross-Border Structuring

## FIN-0238 [必须]
判据: The response states the total dollars needed to repay the $50m term loan plus fees and interest.
提示: response should state the amount needed to replay the $50m loan clearly.
出处: prbench:3cb8f28a6818afe29111c794 | 话题: Corporate Finance

## FIN-0239 [必须]
判据: The response states the near-term problem is cash/liquidity.
提示: checks if the response recognizes the main problem as a cash shortfall.
出处: prbench:3cb8f28a6818afe29111c794 | 话题: Corporate Finance

## FIN-0240 [必须]
判据: The response identifies one-time or non-operating items (e.g., major repair, insurance proceeds).
提示: Separates anomalies from recurring performance.
出处: prbench:3ce91e5ccd6968e432f6749a | 话题: Accounting & Financial Statement Analysis

## FIN-0241 [必须]
判据: The response provides a margin recalculated excluding one-time/non-operating items (e.g., Adjusted EBITDA margin).
提示: Shows sustainable operating results.
出处: prbench:3ce91e5ccd6968e432f6749a | 话题: Accounting & Financial Statement Analysis

## FIN-0242 [负面]
判据: The response treats P&L figures as evidence of cash available (e.g., assuming profit = cash in hand).
提示: Creates serious misunderstanding of financial health.
出处: prbench:3ce91e5ccd6968e432f6749a | 话题: Accounting & Financial Statement Analysis

## FIN-0243 [必须]
判据: The response explicitly discusses whether reported margins (e.g., net income %, EBITDA %) are sustainable or distorted by subsidies, tax credits, or unusual accounting treatments.
提示: Tests ability to identify hidden risks behind seemingly good performance.
出处: prbench:3ce91e5ccd6968e432f6749a | 话题: Accounting & Financial Statement Analysis

## FIN-0244 [必须]
判据: The response identifies gross margin % calculated as (Net Sales − COGS) ÷ Net Sales.
提示: Measures menu/pricing and purchasing efficiency.
出处: prbench:3ce91e5ccd6968e432f6749a | 话题: Accounting & Financial Statement Analysis

## FIN-0245 [必须]
判据: The response identifies net sales after all contra-revenue adjustments.
提示: Establishes the top-line actually earned.
出处: prbench:3ce91e5ccd6968e432f6749a | 话题: Accounting & Financial Statement Analysis

## FIN-0246 [必须]
判据: The response quantifies total contra-revenue as a % of sales.
提示: Shows the materiality of revenue reductions.
出处: prbench:3ce91e5ccd6968e432f6749a | 话题: Accounting & Financial Statement Analysis

## FIN-0247 [必须]
判据: The response calculates the requested numbers correctly (net debt = $175mm, pro forma leverage = $215mm, leverage = 4.3x).
提示: core ask of the prompt.
出处: prbench:3ec38ecf61a256844d9e7639 | 话题: Corporate Finance

## FIN-0248 [必须]
判据: The response explains maintenance covenants usually apply only when the revolving credit facility is drawn by around 35 to 40% (e.g., "the test applies only when the revolving credit facility is at least about 35-40% drawn, or else it is not active").
提示: checks the response' understanding of when maintenance test is normally acive.
出处: prbench:3ec38ecf61a256844d9e7639 | 话题: Corporate Finance

## FIN-0249 [必须]
判据: The response explains how fees affect net debt (e.g., states that netted fees decrease proceeds without increasing new debt, while fees paid from cash increase net debt).
提示: checks correct treatment of fees and cash in leverage.
出处: prbench:3ec38ecf61a256844d9e7639 | 话题: Corporate Finance

## FIN-0250 [必须]
判据: The response does not mix currencies or number scales by using US dollars in millions consistently.
提示: checks consistent units and currency.
出处: prbench:3ec38ecf61a256844d9e7639 | 话题: Corporate Finance

## FIN-0251 [建议]
判据: Mentions materiality — small WIP/unapplied receipt differences might not require detailed separate presentation, but the principle still applies.
提示: insight about changes in wip
出处: prbench:401fe6087be3ed8bce386d32 | 话题: Accounting & Financial Statement Analysis

## FIN-0252 [必须]
判据: Mentions no impact on the CF statement.
提示: explictly asked of by the prompt
出处: prbench:401fe6087be3ed8bce386d32 | 话题: Accounting & Financial Statement Analysis

## FIN-0253 [必须]
判据: Mentions no impact on the p/l unless revenue recognition was distorted.
提示: asked of by the prompt
出处: prbench:401fe6087be3ed8bce386d32 | 话题: Accounting & Financial Statement Analysis

## FIN-0254 [必须]
判据: Quantitatively explains the downward effect on assets e.g. (200).
提示: practical elements
出处: prbench:401fe6087be3ed8bce386d32 | 话题: Accounting & Financial Statement Analysis

## FIN-0255 [必须]
判据: It shows the effect on a liquidity ratio, e.g., current ratio = current assets/current liabilities. As they both go down, the ratio goes down.
提示: needed as this is the scope, a numerical representation
出处: prbench:401fe6087be3ed8bce386d32 | 话题: Accounting & Financial Statement Analysis

## FIN-0256 [必须]
判据: Discusses the effect on the BS: assets and liabilities both go down if this approach is taken.
提示: requested in the prompt
出处: prbench:401fe6087be3ed8bce386d32 | 话题: Accounting & Financial Statement Analysis

## FIN-0257 [必须]
判据: Explains that unapplied receipts are advance payments from customers, treated as a liability until work is performed.
提示: needed as unapplied receipts is talked about
出处: prbench:401fe6087be3ed8bce386d32 | 话题: Accounting & Financial Statement Analysis

## FIN-0258 [必须]
判据: References the principle of substance over form, so unapplied receipts are liabilities, not assets, even if received as cash.
提示: needed for cf management
出处: prbench:401fe6087be3ed8bce386d32 | 话题: Accounting & Financial Statement Analysis

## FIN-0259 [必须]
判据: Explains that WIP represents work performed but not yet invoiced and is therefore treated as an asset under FRS 102 Section 23.
提示: Needed to mention WIP
出处: prbench:401fe6087be3ed8bce386d32 | 话题: Accounting & Financial Statement Analysis

## FIN-0260 [建议]
判据: The response calculates the intellectual property Fair Market Value corresponding to its calculated maximum Enterprise Value for the base-case (k=10%, upfront tax payment), yielding £539.9M (based on FMV=k*Revenue*5.6502).
提示: Calculates an intermediate value.
出处: prbench:41d5456d57e8d4557eba601b | 话题: Taxation & Cross-Border Structuring

## FIN-0261 [必须]
判据: The response correctly calculates the maximum Enterprise Value (assuming upfront tax payment) for the low (8%) royalty rate, yielding £1.390B (based on the derived formula and Post-Migration Value = £1.5B).
提示: Recalculate the outcome under the lower parameter assumption.
出处: prbench:41d5456d57e8d4557eba601b | 话题: Taxation & Cross-Border Structuring

## FIN-0262 [建议]
判据: The response calculates the UK Exit Tax amount corresponding to its calculated maximum Enterprise Value for the base case (k=10%, upfront tax payment).
提示: Calculates the final tax cost consistent with the maximum EV.
出处: prbench:41d5456d57e8d4557eba601b | 话题: Taxation & Cross-Border Structuring

## FIN-0263 [必须]
判据: The response calculates the Present Value factor for the 5-year instalment plan (paying 1/5 of the tax plus 5% interest annually), discounting cash flows at the 12% discount rate provided.
提示: Correctly calculating the Present Value impact of the specific instalment plan is essential.
出处: prbench:41d5456d57e8d4557eba601b | 话题: Taxation & Cross-Border Structuring

## FIN-0264 [必须]
判据: The response defines the break-even condition where the Post-Migration Value (£1.5B) equals the sum of the Enterprise Value and the Present Value of the UK Exit Tax.
提示: Core economic constraint that determines the maximum affordable Enterprise Value.
出处: prbench:41d5456d57e8d4557eba601b | 话题: Taxation & Cross-Border Structuring

## FIN-0265 [必须]
判据: The response algebraically solves the break-even equation, Post-Migration Value=EV+PV(Exit Tax), to express the maximum Enterprise Value as a function of the royalty rate (k) and the Present Value factor of the tax, such as EV max = Post-Migration Value / [1 + (PV Tax Factor*0.25*k*Assumed Revenue Factor*Annuity Factor)] (or equivalent, based on its stated assumptions).
提示: Deriving the closed-form solution.
出处: prbench:41d5456d57e8d4557eba601b | 话题: Taxation & Cross-Border Structuring

## FIN-0266 [必须]
判据: The response identifies the core problem as a circular reference where the maximum Enterprise Value depends on the UK Exit Tax, which itself depends on the IP's Fair Market Value, which in turn depends on EV.
提示: The circularity is the fundamental first step in addressing the prompt's central challenge.
出处: prbench:41d5456d57e8d4557eba601b | 话题: Taxation & Cross-Border Structuring

## FIN-0267 [必须]
判据: The response formulates the intellectual property Fair Market Value using the relief-from-royalty method based on its explicitly stated revenue assumption, the royalty rate (k), and the annuity factor (5.6502).
提示: Correctly constructing the Fair Market Value formula.
出处: prbench:41d5456d57e8d4557eba601b | 话题: Taxation & Cross-Border Structuring

## FIN-0268 [必须]
判据: The response calculates the UK Exit Tax as 25% of the calculated intellectual property Fair Market Value.
提示: Applying the given 25% tax rate to the derived Fair Market Value.
出处: prbench:41d5456d57e8d4557eba601b | 话题: Taxation & Cross-Border Structuring

## FIN-0269 [必须]
判据: The response evaluates the instalment plan by comparing the Present Value of the tax payments under the instalment plan to the upfront tax payment amount (e.g., showing the £ value or % saving).
提示: A quantitative Present Value comparison is necessary.
出处: prbench:41d5456d57e8d4557eba601b | 话题: Taxation & Cross-Border Structuring

## FIN-0270 [必须]
判据: The response calculates the 10-year present value annuity factor at the specified 12% discount rate as 5.6502.
提示: Critical input for the relief-from-royalty Fair Market Value calculation.
出处: prbench:41d5456d57e8d4557eba601b | 话题: Taxation & Cross-Border Structuring

## FIN-0271 [必须]
判据: The response calculates the maximum Enterprise Value for the base-case royalty rate (k=10%), yielding £1.365B.
提示: Provides the specific numerical answer for the base case under the simpler payment scenario.
出处: prbench:41d5456d57e8d4557eba601b | 话题: Taxation & Cross-Border Structuring

## FIN-0272 [必须]
判据: The response calculates the maximum Enterprise Value for the base-case (k=10%), yielding £1.386B.
提示: Provides the specific numerical answer under the more complex payment scenario.
出处: prbench:41d5456d57e8d4557eba601b | 话题: Taxation & Cross-Border Structuring

## FIN-0273 [必须]
判据: The response correctly states that a higher royalty rate assumption (k) leads to a lower maximum affordable Enterprise Value.
提示: Correctly interpreting direction of the sensitivity.
出处: prbench:41d5456d57e8d4557eba601b | 话题: Taxation & Cross-Border Structuring

## FIN-0274 [建议]
判据: The response connects that hedging-frequency error to the convexity premium charged in pricing (e.g., weekly / daily rebalancing leading to discrete hedging errors, gamma / vol-of-vol / path dependency).
提示: valuates ability to interpret the formula economically as a convexity charge.
出处: prbench:431f6cbb5c6dfedf58727f96 | 话题: Derivatives & Structured Products

## FIN-0275 [必须]
判据: The response recognizes that fair-value comparison also depends on equivalent capital / funding charges.
提示: Tests capital-cost awareness as separate economic driver.
出处: prbench:431f6cbb5c6dfedf58727f96 | 话题: Derivatives & Structured Products

## FIN-0276 [必须]
判据: The response recognizes that competitor quote ≠ fair value unless replication methodology is identical.
提示: Tests replication-model comparability; removes capital overlay.
出处: prbench:431f6cbb5c6dfedf58727f96 | 话题: Derivatives & Structured Products

## FIN-0277 [必须]
判据: The response includes market-maker economics (e.g., no bid-offer, inventory, cross-book offset).
提示: Real-world dealer reasoning absent.
出处: prbench:431f6cbb5c6dfedf58727f96 | 话题: Derivatives & Structured Products

## FIN-0278 [必须]
判据: The response states that a futures contract imposes binding obligations at expiry: the long (buyer) must buy/take delivery or cash-settle, and the short (seller) must sell/deliver or cash-settle.
提示: This directly addresses the prompt's explicit request to "explain how futures contracts work" - the foundational requirement that's currently missing.
出处: prbench:432bcf08761684c4cf1b4553 | 话题: Derivatives & Structured Products

## FIN-0279 [负面]
判据: The response incorrectly suggests that stop-loss orders guarantee protection against losses in futures trading.
提示: Common misconception - stop-losses can fail during gaps or extreme volatility, creating false security that could harm investors.
出处: prbench:432bcf08761684c4cf1b4553 | 话题: Derivatives & Structured Products

## FIN-0280 [负面]
判据: The response incorrectly states that futures contracts require physical delivery in most cases.
提示: Most futures contracts are cash-settled; this common misconception would mislead readers about how futures actually work.
出处: prbench:432bcf08761684c4cf1b4553 | 话题: Derivatives & Structured Products

## FIN-0281 [负面]
判据: The response conflates futures with options by suggesting futures provide the right but not the obligation to buy/sell.
提示: This is a fundamental error that completely misrepresents how futures work - futures create obligations, not options.
出处: prbench:432bcf08761684c4cf1b4553 | 话题: Derivatives & Structured Products

## FIN-0282 [必须]
判据: The response states that a short futures position gains when the price falls and loses when the price rises (e.g., “short gains when price falls”).
提示: Distinguishing position types is fundamental; models may mention positions but fail to explain their effect on outcomes.
出处: prbench:432bcf08761684c4cf1b4553 | 话题: Derivatives & Structured Products

## FIN-0283 [必须]
判据: The response states that a long futures position gains when the price rises and loses when the price falls (e.g., “long gains when price rises”).
提示: Distinguishing position types is fundamental; models may mention positions but fail to explain their effect on outcomes.
出处: prbench:432bcf08761684c4cf1b4553 | 话题: Derivatives & Structured Products

## FIN-0284 [必须]
判据: The response states that at each end-of-day settlement, mark-to-market credits gains or debits losses to the trader’s margin account.
提示: Critical mechanism for how gains/losses are realized, supporting the prompt's request about price movement impacts.
出处: prbench:432bcf08761684c4cf1b4553 | 话题: Derivatives & Structured Products

## FIN-0285 [必须]
判据: The response explains the difference between initial margin and variation margin, such as how variation margin is calculated and settled daily.
提示: This technical distinction is crucial for understanding futures mechanics but often glossed over in general explanations.
出处: prbench:432bcf08761684c4cf1b4553 | 话题: Derivatives & Structured Products

## FIN-0286 [必须]
判据: The response includes a correct numeric example quantifying leverage amplification (e.g., a 10% move in price at 10× leverage causes a 100% P&L change).
提示: Understanding leverage is central to futures trading. Including an example tests whether the model goes beyond generic statements.
出处: prbench:432bcf08761684c4cf1b4553 | 话题: Derivatives & Structured Products

## FIN-0287 [必须]
判据: The response calculates the collateral shortfall as "$3 billion."
提示: This is an objective, binary check for the correct quantification of the immediate funding gap, a core financial calculation essential for crisis management.
出处: prbench:43d4ee610f860278d4c8e7eb | 话题: Risk Management & Stress Testing

## FIN-0288 [必须]
判据: The response identifies how Monero should be classified on the balance sheet under IFRS or GAAP (e.g., as an intangible asset, including supporting rationale).
提示: Proper classification affects asset valuation, depreciation, and compliance with accounting standards.
出处: prbench:4426caae2ebc98d166819139 | 话题: Accounting & Financial Statement Analysis

## FIN-0289 [必须]
判据: The response analyses the impact of Monero’s default anonymity on the company’s cash flow statement categorization (e.g., operating vs. investing activities).
提示: Understanding flow classification avoids misstatements in core financial reports.
出处: prbench:4426caae2ebc98d166819139 | 话题: Accounting & Financial Statement Analysis

## FIN-0290 [必须]
判据: The response outlines how a company can recognize Monero-based payments under accrual accounting (e.g., by converting XMR to fiat at transaction time and recording revenue at fair value).
提示: Revenue recognition determines when earnings appear in reports—critical for investor confidence.
出处: prbench:4426caae2ebc98d166819139 | 话题: Accounting & Financial Statement Analysis

## FIN-0291 [建议]
判据: The response specifies subsequent measurement of Monero holdings at reporting dates (e.g., an IFRS intangible with impairment where applicable).
提示: This is explicitly asked.
出处: prbench:4426caae2ebc98d166819139 | 话题: Accounting & Financial Statement Analysis

## FIN-0292 [负面]
判据: The response contains internally consistent numeric calculations (e.g., calculations for yields, fees) under stated assumptions.
提示: This ensures the reasoning is correct.
出处: prbench:44452e3c48c11e63b75bf068 | 话题: Wealth Management, Financial Planning & Advice

## FIN-0293 [必须]
判据: The response explains that the CMBS structure creates a funding arbitrage because the REIT earns 5.2% on the full $500M loan pool while paying 4.8% on only the $450M of sold securities.
提示: Tests understanding of the core spread-capture mechanism arising from different rate bases.
出处: prbench:4472ff1b6ddb7fc595843cf6 | 话题: Corporate Finance

## FIN-0294 [必须]
判据: The response explains that retaining the $50M subordinate tranche reduces upfront liquidity available to the REIT.
提示: Tests recognition of how retaining capital limits immediate deployment for other uses.
出处: prbench:4472ff1b6ddb7fc595843cf6 | 话题: Corporate Finance

## FIN-0295 [负面]
判据: The response claims that all CMBS equity returns change solely because of prepayment.
提示: Penalizes response that attributing all CMBS income variations to prepapayments, ignoring fixed interest on sold tranches and other structural effects.
出处: prbench:4472ff1b6ddb7fc595843cf6 | 话题: Corporate Finance

## FIN-0296 [必须]
判据: The response recommends CMBS over the corporate bond under the stated base-case parameters (5.2% loan yield, 4.8% CMBS coupon on $450M sold, $50M retained tranche, 5% expected prepayment, 5.6% corporate bond coupon, 120 bps CMBS upfront cost, 40 bps corporate bond upfront cost) due to quantitative analysis showing CMBS generates a lower net cost.
提示: Give recommendation as required by the user and test correct selection of the preferred option under base-case financial assumption.
出处: prbench:4472ff1b6ddb7fc595843cf6 | 话题: Corporate Finance

## FIN-0297 [必须]
判据: The response compares total annual interest outlay under CMBS versus the corporate bond by showing that paying 4.8% on $450M results in lower total interest expense than paying 5.6% on $500M.
提示: Tests numeric comparison of funding costs between the two options.
出处: prbench:4472ff1b6ddb7fc595843cf6 | 话题: Corporate Finance

## FIN-0298 [建议]
判据: The response explains that the retained $50M tranche continues to earn the full 5.2% yield.
提示: Tests understanding that retained capital generates ongoing income, independent of upfront liquidity constraint.
出处: prbench:4472ff1b6ddb7fc595843cf6 | 话题: Corporate Finance

## FIN-0299 [必须]
判据: The response explains that, in the baseline scenario, the corporate bond's 5.6% coupon must be paid on the full $500M regardless of loan prepayments.
提示: Tests awareness that bond obligations remain fixed as underlying loan balances declines, distinct from CMBS variability.
出处: prbench:4472ff1b6ddb7fc595843cf6 | 话题: Corporate Finance

## FIN-0300 [必须]
判据: The response explains that the present value of after-tax cash flows must be used to evaluate the economic cost of both options over a 5-year horizon.
提示: Tests recognition that timing of payments affects economic comparison.
出处: prbench:4472ff1b6ddb7fc595843cf6 | 话题: Corporate Finance

## FIN-0301 [必须]
判据: The response explains that the 40-bps spread on the $450M sold CMBS portion does not fully accrue to the REIT because a portion covers fees and servicing.
提示: Tests understanding that CMBS spead are partly consumed by structural costs rather than entirely retained as equity return.
出处: prbench:4472ff1b6ddb7fc595843cf6 | 话题: Corporate Finance

## FIN-0302 [负面]
判据: The response treats auctions as identical to continuous trading.
提示: Auctions are important around the windows in question.
出处: prbench:456351b44c40c137648b2f8d | 话题: Market Microstructure, Trading & Liquidity

## FIN-0303 [必须]
判据: The response differentiates venues correctly - it separately treats continuous lit, auctions (open/close), and midpoint/dark behaviour.
提示: Venue mechanics differ, conflation breaks the analysis.
出处: prbench:456351b44c40c137648b2f8d | 话题: Market Microstructure, Trading & Liquidity

## FIN-0304 [必须]
判据: The response states that wider ticks increase effective spreads.
提示: Main microstructure linkage must be correct.
出处: prbench:456351b44c40c137648b2f8d | 话题: Market Microstructure, Trading & Liquidity

## FIN-0305 [建议]
判据: The response identifies net working capital (NWC) movement as the main reason for the gap between net income and operating cash flow (without listing parts, AR/inventory/AP are covered in other items).
提示: Most such gaps come from working capital changes, a good response should call that out clearly.
出处: prbench:46fb5981c5ca74280343b416 | 话题: Accounting & Financial Statement Analysis

## FIN-0306 [必须]
判据: The response lists a decrease in accounts payable (or slower growth relative to costs) as a contributing cause.
提示: While slightly less common than A/R or Inventory issues, A/P movement is a key part of a comprehensive NWC analysis and should be included for a high-quality response.
出处: prbench:46fb5981c5ca74280343b416 | 话题: Accounting & Financial Statement Analysis

## FIN-0307 [建议]
判据: The response mentions that non-cash expenses (e.g., depreciation) are added back to net income to calculate OCF and are therefore not a cause of the negative divergence.
提示: Clarifying this common point of confusion shows precision but is secondary to the main causes (working capital).
出处: prbench:46fb5981c5ca74280343b416 | 话题: Accounting & Financial Statement Analysis

## FIN-0308 [建议]
判据: The response calculates one possible share price as $12 million/1.5 million shares = $8.
提示: Important to gauge the deal at hand
出处: prbench:48d35e06e7554057d5bdb1a6 | 话题: Corporate Finance

## FIN-0309 [建议]
判据: The response mentions that 17.65% is the lower bound for investor ownership.
提示: Lowest possible investor ownership, though inherently motivated to maximize
出处: prbench:48d35e06e7554057d5bdb1a6 | 话题: Corporate Finance

## FIN-0310 [必须]
判据: The response states that one conversion approach is calculating the share price based on the agreed-upon pre-money valuation (e.g., discounted equity price method, cap-based conversion method).
提示: One of the three common conversion methods (pre-money)
出处: prbench:48d35e06e7554057d5bdb1a6 | 话题: Corporate Finance

## FIN-0311 [建议]
判据: The response calculates one possible share price as $16.5 million/2.152 million shares = $7.67.
提示: Important to gauge the deal at hand
出处: prbench:48d35e06e7554057d5bdb1a6 | 话题: Corporate Finance

## FIN-0312 [必须]
判据: The response identifies that the ideal conversion method gives the investor $3 million/$16.5 million = 18.18%.
提示: Ideal scenario
出处: prbench:48d35e06e7554057d5bdb1a6 | 话题: Corporate Finance

## FIN-0313 [负面]
判据: The response identifies that the ideal scenario has a share price of $8.
提示: Reinforces overvaluation
出处: prbench:48d35e06e7554057d5bdb1a6 | 话题: Corporate Finance

## FIN-0314 [建议]
判据: The response calculates one possible share price as $15 million/2.25 million shares = $6.67.
提示: Important to gauge the deal at hand
出处: prbench:48d35e06e7554057d5bdb1a6 | 话题: Corporate Finance

## FIN-0315 [建议]
判据: The response states that the lower bound for the post-money valuation is $15 million.
提示: Financial metric that factors into the investor's decision
出处: prbench:48d35e06e7554057d5bdb1a6 | 话题: Corporate Finance

## FIN-0316 [必须]
判据: The response specifies that hedge effectiveness must remain within the 80-125% range.
提示: Quantifying the threshold.
出处: prbench:491cc298f862e2baa18881a3 | 话题: International Finance & FX Hedging

## FIN-0317 [必须]
判据: The response provides the lower-of-the-two test formula for the effective portion, which is min(|ΔFV(hedging instrument)|, |ΔPV(hedged item)|).
提示: Has to talk about mechanics.
出处: prbench:491cc298f862e2baa18881a3 | 话题: International Finance & FX Hedging

## FIN-0318 [必须]
判据: The response amortizes excluded forward points from OCI to P&L.
提示: Requires systemic amortization.
出处: prbench:491cc298f862e2baa18881a3 | 话题: International Finance & FX Hedging

## FIN-0319 [必须]
判据: The response states that forward points are excluded from hedge designation (e.g., as a cost of hedging).
提示: Treatment mechanics as asked.
出处: prbench:491cc298f862e2baa18881a3 | 话题: International Finance & FX Hedging

## FIN-0320 [必须]
判据: The response defines a 6-month hypothetical derivative (e.g., a 6-month NDF, a 6-month spot forward on CNY) for effectiveness testing.
提示: Required for lower-of test comparison.
出处: prbench:491cc298f862e2baa18881a3 | 话题: International Finance & FX Hedging

## FIN-0321 [建议]
判据: The response incorporates financing fees (e.g., advisory costs or transaction expenses) into the LBO model.
提示: To show their impact on equity returns.
出处: prbench:4924c9a358e16f7de6ce386c | 话题: Corporate Finance

## FIN-0322 [必须]
判据: The response reconstructs normalized historical financials for the target firm, including adjustments for asset sales, litigation, or restructuring costs, to present consistent historical free cash flows.
提示: Ensures the foundation of the LBO model is accurate and traceable.
出处: prbench:4924c9a358e16f7de6ce386c | 话题: Corporate Finance

## FIN-0323 [必须]
判据: The response should state that the user will be eligible for close to 8.8k in Old Age Security upon retirement.
提示: Important for model to recognize all income sources - all Canadians are eligible for OAS
出处: prbench:49f45c6830962486ce79cb07 | 话题: Wealth Management, Financial Planning & Advice

## FIN-0324 [必须]
判据: The response should state that the user could receive up to a maximum of 17k per year from the Canada Pension Plan upon retirement.
提示: Important for model to recognize all income sources - all working Canadians are eligible for CPP
出处: prbench:49f45c6830962486ce79cb07 | 话题: Wealth Management, Financial Planning & Advice

## FIN-0325 [必须]
判据: The response must estimate that the RRSP can be converted to an annuity for 15k-20k per year.
提示: Important to understand the income from all sources. Model should come close to the range given using standard calculators
出处: prbench:49f45c6830962486ce79cb07 | 话题: Wealth Management, Financial Planning & Advice

## FIN-0326 [必须]
判据: The response calculates that income from all sources will be approximately 40k pension + 17k CPP + 20k RRSP Annuity + 10k TFSA + 8.8k OAS = 95.8k on the high end.
提示: User needs to understand approximate post retirement income
出处: prbench:49f45c6830962486ce79cb07 | 话题: Wealth Management, Financial Planning & Advice

## FIN-0327 [必须]
判据: The response indicates that the TFSA can be converted to an annuity upon retirement.
提示: Educates the user on how the TFSA converts to income
出处: prbench:49f45c6830962486ce79cb07 | 话题: Wealth Management, Financial Planning & Advice

## FIN-0328 [必须]
判据: The response must estimate that the TFSA can be converted to an annuity for 7.5k-10k per year.
提示: Important to understand the income from all sources. Model should come close to the range given using standard calculators
出处: prbench:49f45c6830962486ce79cb07 | 话题: Wealth Management, Financial Planning & Advice

## FIN-0329 [必须]
判据: The response explains that the 70% rule states that you should have 70% of your pre-retirement income to maintain your post-retirement lifestyle.
提示: Since the user doesn't want to take a hit, it is important to understand general rule of thumb on maintaining post retirement lifestyle
出处: prbench:49f45c6830962486ce79cb07 | 话题: Wealth Management, Financial Planning & Advice

## FIN-0330 [必须]
判据: The response indicates that the user's retirement income will be about 58%-64% of pre-retirement income.
提示: User doesn't want to take a big hit on income in retirement so needs to understand what percentage post retirment income will be compared to pre retirement
出处: prbench:49f45c6830962486ce79cb07 | 话题: Wealth Management, Financial Planning & Advice

## FIN-0331 [必须]
判据: The response calculates that income from all sources will be approximately 40k pension+17k CPP+15k RRSP Annuity+7.5k TFSA+8.8k OAS = 88.3k on the low end.
提示: User needs to understand approximate post retirement income
出处: prbench:49f45c6830962486ce79cb07 | 话题: Wealth Management, Financial Planning & Advice

## FIN-0332 [必须]
判据: The response states the overall cost of capital stays roughly unchanged if the credit rating and loan rates are unchanged.
提示: checks correct direction for company's overall required return.
出处: prbench:4b1455d50ef76dd6a55b678e | 话题: Corporate Finance

## FIN-0333 [建议]
判据: The response states that one step lower in rating usually increases new borrowing costs by about 1.5 percentage points.
提示: connects rating risk to borrowing costs.
出处: prbench:4b1455d50ef76dd6a55b678e | 话题: Corporate Finance

## FIN-0334 [必须]
判据: The response states that after-tax borrowing cost equals 4.875% by showing 6.5% * (1 - 25%) = 4.875%.
提示: checks the borrowing cost used in calculations reflects taxes.
出处: prbench:4b1455d50ef76dd6a55b678e | 话题: Corporate Finance

## FIN-0335 [必须]
判据: The response explicitly calculates the after-tax cash income as $75MM * 4% * (1-25%) = $2.25MM.
提示: checks the math on the lost interest income
出处: prbench:4b1455d50ef76dd6a55b678e | 话题: Corporate Finance

## FIN-0336 [必须]
判据: The response states that spending $75MM raises net debt by $75MM.
提示: show that using cash increases debt after subtracting cash.
出处: prbench:4b1455d50ef76dd6a55b678e | 话题: Corporate Finance

## FIN-0337 [必须]
判据: The response states that higher EPS can still reduce value if the discount rate increases.
提示: corrects a common misunderstanding.
出处: prbench:4b1455d50ef76dd6a55b678e | 话题: Corporate Finance

## FIN-0338 [必须]
判据: The response explicitly states interest expense does not rise immediately because the company did not add new debt and rates did not change.
提示: separates spending cash from paying more interest.
出处: prbench:4b1455d50ef76dd6a55b678e | 话题: Corporate Finance

## FIN-0339 [必须]
判据: The response states whether the following ratios are inside or outside common ranges for companies at the current rating level (BB) after the buyback: net debt to operating cash profit; cash flow to net debt; interest coverage.
提示: put the numbers in context the rating uses.
出处: prbench:4b1455d50ef76dd6a55b678e | 话题: Corporate Finance

## FIN-0340 [必须]
判据: The response states EPS increases only if current net profit is greater than $2.25MM divided by the buyback percent (10%), which makes it $22.5MM.
提示: confirm the point where buyback starts increasing EPS
出处: prbench:4b1455d50ef76dd6a55b678e | 话题: Corporate Finance

## FIN-0341 [必须]
判据: The response does not lower operating profit because the company gives up interest on cash.
提示: operating profit does not measure cash earnings.
出处: prbench:4b1455d50ef76dd6a55b678e | 话题: Corporate Finance

## FIN-0342 [必须]
判据: The response defines a numeric adverse selection variable as a model input (e.g., informed trade probability or an order flow toxicity measure).
提示: Information asymmetry must be parameterized to test the channel.
出处: prbench:4b87e76d5559e05d6b14da57 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0343 [必须]
判据: The response explains how queue position changes the fill probability (e.g., deeper quotes or lower queue ranks have lower execution likelihood, canceled orders reduce fill odds during volatility bursts).
提示: Explaining how queue position influences fill probability shows the model’s realism and connects theory to observable execution patterns.
出处: prbench:4b87e76d5559e05d6b14da57 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0344 [负面]
判据: Response suggests that NBFCs apply for RBI's marginal standing facility, a funding mechanism for which NBFCs are ineligible.
提示: Ineligible programs need to be penalised
出处: prbench:4bf706d56d7e55545b9e1da8 | 话题: Corporate Finance

## FIN-0345 [建议]
判据: States that the Federal Reserve aims to choose a policy that minimizes the value of the loss function.
提示: Clarifies the use of the loss function
出处: prbench:4e08de8b82b6f7dd361ee0c3 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0346 [必须]
判据: The response calculates the number of shares issued to the Series A investors as 250,000, based on the CHF 2 million investment at a CHF 8.00 share price.
提示: This is a necessary component of the post-investment cap table.
出处: prbench:4e3e17f08d8c2eeb8dd56306 | 话题: Alternative Investments & Private Markets

## FIN-0347 [必须]
判据: The response correctly calculates the conversion price for the mezzanine notes as CHF 5.60 by applying the 30% discount to the Series A share price of CHF 8.00.
提示: This is a key term of the mezzanine notes and a critical input for the dilution analysis.
出处: prbench:4e3e17f08d8c2eeb8dd56306 | 话题: Alternative Investments & Private Markets

## FIN-0348 [必须]
判据: The response correctly calculates the Series A share price as CHF 8.00, derived from the CHF 8 million pre-money valuation and 1 million pre-investment shares.
提示: This is a fundamental calculation for the entire cap table.
出处: prbench:4e3e17f08d8c2eeb8dd56306 | 话题: Alternative Investments & Private Markets

## FIN-0349 [必须]
判据: The response explains that the choice of conversion method (e.g., pre-money vs. post-money method) directly impacts the dilution of the founders and the ownership of the mezzanine investors.
提示: This tests the conceptual understanding of how different conversion mechanics affect the cap table.
出处: prbench:4e3e17f08d8c2eeb8dd56306 | 话题: Alternative Investments & Private Markets

## FIN-0350 [必须]
判据: The response explicitly states that the accrued interest on the mezzanine notes must be included in the total amount to be converted, in addition to the CHF 1 million principal.
提示: Acknowledging the impact of accrued interest is crucial for an accurate cap table calculation.
出处: prbench:4e3e17f08d8c2eeb8dd56306 | 话题: Alternative Investments & Private Markets

## FIN-0351 [必须]
判据: The response identifies that under IFRS 9 / IAS 32, the reset is an embedded derivative requiring fair-value re-measurement through the P&L statement.
提示: IFRS compliance is compulsory.
出处: prbench:507a5d6715e44ddb805b57e6 | 话题: Corporate Finance

## FIN-0352 [必须]
判据: The response avoids saying the reset “protects investors” or “reduces risk” unless it is clearly qualified as bondholder-specific.
提示: This protects from taking the CFO's as a neutral or base position.
出处: prbench:507a5d6715e44ddb805b57e6 | 话题: Corporate Finance

## FIN-0353 [必须]
判据: The model explains that reclassification from debt to equity will alter debt-to-equity ratios.
提示: This shows understanding of balance-sheet sensitivity.
出处: prbench:507a5d6715e44ddb805b57e6 | 话题: Corporate Finance

## FIN-0354 [必须]
判据: The response explicitly quantifies the effective cost of capital increase caused by the reset (e.g., adding greater than 1.5% to the weighted average cost of capital vs. a plain convertible bond).
提示: A numerical understanding of how the reset changes capital cost is highly important.
出处: prbench:507a5d6715e44ddb805b57e6 | 话题: Corporate Finance

## FIN-0355 [必须]
判据: The model explains that under extreme dilution, the instrument could be reclassified from debt to equity (e.g., the dilution condition depends on specific accounting standards such as IFRS vs. US GAAP, and contract terms).
提示: This shows understanding of balance-sheet sensitivity.
出处: prbench:507a5d6715e44ddb805b57e6 | 话题: Corporate Finance

## FIN-0356 [必须]
判据: The response calculates the Singapore fund manager's annual tax liability on management fees for the $150M fund, applying a tax rate to the fee income and expressing the result in dollars (such as applying a 10% concessionary rate to $3M in management fees yielding a $300,000 tax liability).
提示: Calculate actual tax on $3M fees
出处: prbench:52d6d76008ec42eb3814e8ef | 话题: Taxation & Cross-Border Structuring

## FIN-0357 [必须]
判据: The response calculates the annual employment cost for the minimum Singapore substance professional headcount, showing salary estimates multiplied by the number of professionals required (such as 3 professionals × SGD 120,000 average = SGD 360,000 or ~USD 270,000).
提示: Calculate 3 × average salary personnel
出处: prbench:52d6d76008ec42eb3814e8ef | 话题: Taxation & Cross-Border Structuring

## FIN-0358 [必须]
判据: The response explains the specific US tax mechanism for the feeder fund, such as a check-the-box election, which allows the offshore fund to be treated as a partnership for US tax purposes.
提示: The key technical step for PFIC mitigation that an expert would specify.
出处: prbench:52d6d76008ec42eb3814e8ef | 话题: Taxation & Cross-Border Structuring

## FIN-0359 [必须]
判据: The response quantifies the manager-level tax by calculating the approximate tax on a hypothetical £1M of performance fees in Singapore, applying a specific concessionary Financial Sector Incentive (FSIE) scheme rate, such as 10% or 13.5%.
提示: A quantitative check of the manager-level taxation requirement.
出处: prbench:52d6d76008ec42eb3814e8ef | 话题: Taxation & Cross-Border Structuring

## FIN-0360 [必须]
判据: The response explains that the RRP lets large investors trade cash for Treasuries overnight.
提示: This checks of the model understands the basic function of the RRP in moving liquidity between the market and the Fed.
出处: prbench:53d4d50655dbe8a1b6e45757 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0361 [必须]
判据: The response explains that reserve impacts appear within days of settlement.
提示: This adds temporal reasoning.
出处: prbench:53d4d50655dbe8a1b6e45757 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0362 [必须]
判据: The response states that rising reverse-repo balances show that liquidity is trapped at the Fed instead of reaching dealers.
提示: This tests causal interpretation, not just mention of RRP.
出处: prbench:53d4d50655dbe8a1b6e45757 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0363 [必须]
判据: The response identifies a bill-heavy issuance mix as reducing duration supply (e.g., a drop in weighted-average maturity and lower term premiums).
提示: This tests understanding of issuance composition.
出处: prbench:53d4d50655dbe8a1b6e45757 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0364 [必须]
判据: The response identifies the Reverse Repo Facility (RRP) as a Federal Reserve tool.
提示: This checks if the model names the RRP as part of the Fed’s operations.
出处: prbench:53d4d50655dbe8a1b6e45757 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0365 [必须]
判据: The response states that term-premium compression drives the yield decline (e.g., investors buying treasuries for duration hedging, financial institutions holding risk-free assets to meet liquidity regulations).
提示: This ensures correct decomposition component.
出处: prbench:53d4d50655dbe8a1b6e45757 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0366 [负面]
判据: The response characterizes the Supplementary Leverage Ratio (SLR) as a dynamic, risk-weighted tool (e.g., saying the SLR automatically relaxes during stress or doesn’t apply to Treasuries).
提示: This checks if the model understands what SLR rules actually cover
出处: prbench:53d4d50655dbe8a1b6e45757 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0367 [必须]
判据: The response names repo specialness as evidence of collateral scarcity (e.g., high FTD rates indicating inability to source collateral, lenders accepting lower returns on specials, signaling a scarcity premium on collateral).
提示: Saying “repo specialness” shows the model knows how to spot scarcity in actual data, not just talk about it.
出处: prbench:53d4d50655dbe8a1b6e45757 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0368 [必须]
判据: The response calculates or describes a directional example of dealer balance-sheet cost (e.g., each $1 billion of Treasuries adds 20 bps of leverage exposure, each $1B of inventory adds 3-5 bps of dealer funding costs).
提示: This involves solid cost logic.
出处: prbench:53d4d50655dbe8a1b6e45757 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0369 [必须]
判据: The response describes how a fall in reserves tightens bank liquidity (e.g., higher funding spreads, increased internal transfer pricing).
提示: This helps to separate mechanical flow from market impact.
出处: prbench:53d4d50655dbe8a1b6e45757 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0370 [必须]
判据: Assesses whether the overall cost of capital is appropriate for this distressed scenario.
提示: Evaluates understanding of risk-adjusted pricing in distressed situations.
出处: prbench:53df689147ec64c8e7e239a6 | 话题: Corporate Finance

## FIN-0371 [必须]
判据: Maintains accuracy in legal and financial statements without material misstatements regarding sacred rights, voting thresholds, or agent authorities.
提示: Ensures technical accuracy without requiring incorrect statements.
出处: prbench:53df689147ec64c8e7e239a6 | 话题: Corporate Finance

## FIN-0372 [必须]
判据: The response states that Irish dividend WHT can be reduced to 0% via domestic exemptions (not only by treaty).
提示: Many models misstate this as “5% by treaty”; accurate exemption detail is key to cash flow.
出处: prbench:543863496e70ad7d66e80b6b | 话题: Taxation & Cross-Border Structuring

## FIN-0373 [负面]
判据: The response treats GILTI (Global Intangible Low-Taxed Income) and FDII (Foreign-Derived Intangible Income) as the same or directly linked regimes.
提示: Confusion signals a lack of expertise; misleads user on U.S. tax exposure.
出处: prbench:543863496e70ad7d66e80b6b | 话题: Taxation & Cross-Border Structuring

## FIN-0374 [必须]
判据: The response identifies that GILTI FTCs are limited to 80%.
提示: Determines incremental U.S. tax cost.
出处: prbench:543863496e70ad7d66e80b6b | 话题: Taxation & Cross-Border Structuring

## FIN-0375 [必须]
判据: The response states that DEMPE functions in Ireland justify reallocating profits from Singapore.
提示: DEMPE is the core test in transfer pricing disputes; omission or misapplication makes the response unusable.
出处: prbench:543863496e70ad7d66e80b6b | 话题: Taxation & Cross-Border Structuring

## FIN-0376 [必须]
判据: The response notes that Singapore imposes 0% dividend withholding tax.
提示: Misstating this is a common AI error; repatriation planning depends on this fact.
出处: prbench:543863496e70ad7d66e80b6b | 话题: Taxation & Cross-Border Structuring

## FIN-0377 [必须]
判据: The response states that the GILTI high-tax exclusion applies if the foreign ETR is ≥18.9%.
提示: GILTI is the binding constraint for the U.S. parent; superficial treatment misses the true pain point.
出处: prbench:543863496e70ad7d66e80b6b | 话题: Taxation & Cross-Border Structuring

## FIN-0378 [建议]
判据: The response states that Singapore royalties face ~10% WHT unless reduced by treaty.
提示: Explains why groups avoid royalties; adds credibility.
出处: prbench:543863496e70ad7d66e80b6b | 话题: Taxation & Cross-Border Structuring

## FIN-0379 [必须]
判据: The response models a credit stress scenario showing portfolio impact with spreads widening three hundred basis points, with a default three-year duration translating to a nine percent hit, including NAV change, drawdown, P&L, liquidity coverage, solvency ratio, and whether a trigger occurs over a specific timeline.
提示: Tests portfolio resilience under credit market stress.
出处: prbench:5478614c5f8c6f12b4b40033 | 话题: Risk Management & Stress Testing

## FIN-0380 [必须]
判据: The response defines a stablecoin buffer sizing methodology to maintain twenty percent liquidity with ninety-five percent confidence.
提示: Quantitative framework for liquidity reserve adequacy calculation.
出处: prbench:5478614c5f8c6f12b4b40033 | 话题: Risk Management & Stress Testing

## FIN-0381 [必须]
判据: The response calculates the NPV of cumulative repatriated cash using a 15% discount rate.
提示: Incorporating NPV reflects time value of money and provides a standardized measure of long-term cash efficiency.
出处: prbench:548f3c9176bc5f6fcb5f7d2d | 话题: Taxation & Cross-Border Structuring

## FIN-0382 [必须]
判据: The response explains that the UAE 0 % rate fails the 15 % test (e.g., the failed test is causing ≈ 17 % Singapore CIT to apply).
提示: This connects legal failure to tax result.
出处: prbench:56f76bcf986cb3f17d4d25ef | 话题: Taxation & Cross-Border Structuring

## FIN-0383 [必须]
判据: The response states both Singapore foreign-source tests: (1) income received in Singapore and (2) taxed at ≥ 15 % in the source jurisdiction.
提示: This ensures full rule coverage.
出处: prbench:56f76bcf986cb3f17d4d25ef | 话题: Taxation & Cross-Border Structuring

## FIN-0384 [必须]
判据: The response compares the Singapore CFC control threshold of ≥ 50 % ownership with the passive-income ratio test of > 50 %.
提示: This confirms dual CFC tests.
出处: prbench:56f76bcf986cb3f17d4d25ef | 话题: Taxation & Cross-Border Structuring

## FIN-0385 [必须]
判据: The response uses the CAPM (Re = Rf + β×(Rm–Rf)) to calculate the cost of equity.
提示: Most LLMs don't dynamically adjust Re.
出处: prbench:585756d1642eddbab570754e | 话题: Corporate Finance

## FIN-0386 [建议]
判据: The response calculates the tax-adjusted cost of debt as 5.625%.
提示: LLMs often forget tax adjustments.
出处: prbench:585756d1642eddbab570754e | 话题: Corporate Finance

## FIN-0387 [建议]
判据: The response states that debt financing increases ROE.
提示: Since the project ROIC is higher than after-tax cost of debt (e.g., 11% > 5.625%).
出处: prbench:585756d1642eddbab570754e | 话题: Corporate Finance

## FIN-0388 [必须]
判据: The response calculates a WACC of 9.20% under equity financing.
提示: Crucial for value calculations.
出处: prbench:585756d1642eddbab570754e | 话题: Corporate Finance

## FIN-0389 [必须]
判据: The response calculates the financial loss avoided by the client trading on inside information as approximately £2.8M.
提示: Quantifies the insider deal's value, relevant for penalties.
出处: prbench:5896ff39bb1c5472d7fd7cf6 | 话题: Regulation, Compliance & Ethics

## FIN-0390 [必须]
判据: The response quantifies the firm's direct financial loss from the proprietary desk's position as £8.4M.
提示: This contextualises the scale of the firm's internal failure.
出处: prbench:5896ff39bb1c5472d7fd7cf6 | 话题: Regulation, Compliance & Ethics

## FIN-0391 [必须]
判据: The response calculates the firm’s potential FCA fine exposure using the UK MAR Article 30 framework by stating the maximum sanction as the higher of £15 million or 15% of total annual turnover.
提示: MAR Article 30 quantifies the regulatory penalty exposure.
出处: prbench:5896ff39bb1c5472d7fd7cf6 | 话题: Regulation, Compliance & Ethics

## FIN-0392 [负面]
判据: The response states that the compliance officer has primary liability for insider dealing.
提示: wrong assessment of liable person.
出处: prbench:5896ff39bb1c5472d7fd7cf6 | 话题: Regulation, Compliance & Ethics

## FIN-0393 [必须]
判据: The response states that financial compensation for a whistleblowing dismissal is unlimited, in contrast to the statutory cap for ordinary unfair dismissal.
提示: Quantifies the unique financial remedy available to whistleblowers.
出处: prbench:5896ff39bb1c5472d7fd7cf6 | 话题: Regulation, Compliance & Ethics

## FIN-0394 [必须]
判据: The response correctly identifies key drivers of IRR (e.g., EBITDA growth, debt paydown, exit multiple) in the explanation.
提示: Understanding IRR drivers is essential for evaluating the investment's sensitivity and risks, providing deeper insight.
出处: prbench:5cf478460448b33657912b1c | 话题: Corporate Finance

## FIN-0395 [必须]
判据: The response correctly uses the target's net debt of $310M in the equity value derivation (e.g., equity value = enterprise value (EV) - net debt).
提示: This ensures the net debt correctly used.
出处: prbench:5cf478460448b33657912b1c | 话题: Corporate Finance

## FIN-0396 [必须]
判据: The response uses realistic assumptions for accretion (e.g., interest rate ~7-9%, tax rate ~25-27%).
提示: Assumptions must be reasonable and transparent to allow for reproducibility and credibility of the analysis.
出处: prbench:5cf478460448b33657912b1c | 话题: Corporate Finance

## FIN-0397 [必须]
判据: The response correctly calculates the entry EV/EBITDA multiple as approximately $850M / $95M = 8.95x.
提示: The entry multiple is a key benchmark for valuation and must be accurate to ensure all subsequent analysis is based on correct premises.
出处: prbench:5cf478460448b33657912b1c | 话题: Corporate Finance

## FIN-0398 [建议]
判据: The response correctly calculates the equity check as EV $850M minus max debt $522.5M equals $327.5M (where max debt = 5.5x * $95M EBITDA).
提示: The equity investment size is crucial for accretion and IRR analysis, and an error here affects all return calculations.
出处: prbench:5cf478460448b33657912b1c | 话题: Corporate Finance

## FIN-0399 [必须]
判据: The response clearly distinguishes IRR from WACC in methodology (i.e., WACC is not used to compute IRR).
提示: This follow's the prompt requests.
出处: prbench:5cf478460448b33657912b1c | 话题: Corporate Finance

## FIN-0400 [必须]
判据: The response recommends treating undocumented intercompany balances/loans as debt-like items in the Completion Accounts adjustment.
提示: Reflects the economic substance of unverified claims.
出处: prbench:5d6d37d5ea4b850751e5746b | 话题: Corporate Finance

## FIN-0401 [必须]
判据: The response fixes the earn-out FX treatment by specifying that local currency ARR figures will be translated into GBP using a fixed exchange rate set at signing.
提示: Neutralising FX volatility is crucial.
出处: prbench:5d6d37d5ea4b850751e5746b | 话题: Corporate Finance

## FIN-0402 [建议]
判据: The response defines the Annual Recurring Revenue metric for the earn-out to strictly include subscription revenue only, explicitly excluding one-time items like implementation fees.
提示: Precise ARR definition.
出处: prbench:5d6d37d5ea4b850751e5746b | 话题: Corporate Finance

## FIN-0403 [建议]
判据: The response includes GAAP guardrails for the earn-out measurement, requiring consistent application of specified accounting standards (e.g., IFRS 15/ASC 606) throughout the earn-out period.
提示: Audit rights are essential for verification.
出处: prbench:5d6d37d5ea4b850751e5746b | 话题: Corporate Finance

## FIN-0404 [必须]
判据: If the transaction is a taxable sale, the response calculates recognized gain as $18 million (FMV $20M − $2M basis); if it is a 351/361 outbound transfer of intangibles, the response states no immediate gain and applies 367(d) deemed royalties.
提示: Accurate gain calculation is foundational for tax projections; errors cascade through subsequent analyses.
出处: prbench:5de6ea87151756dbb8d40455 | 话题: Taxation & Cross-Border Structuring

## FIN-0405 [必须]
判据: The response explains that German CFC inclusions are taxed at the shareholder’s applicable German rates (e.g., CIT 15% + solidarity + municipal trade tax), not a fixed 25%.
提示: Provides specific tax impact for risk assessment.
出处: prbench:5de6ea87151756dbb8d40455 | 话题: Taxation & Cross-Border Structuring

## FIN-0406 [负面]
判据: The response claims the IP transfer is fully tax-free without conditions.
提示: Ignores IRS anti-abuse rules, risking non-compliance.
出处: prbench:5de6ea87151756dbb8d40455 | 话题: Taxation & Cross-Border Structuring

## FIN-0407 [必须]
判据: For 367(d), the response determines deemed royalties using an arm’s-length royalty under 482 over the useful life (or regulatory cap), not by dividing built-in gain by years.
提示: Ensures precise annual tax projections based on gain and useful life.
出处: prbench:5de6ea87151756dbb8d40455 | 话题: Taxation & Cross-Border Structuring

## FIN-0408 [必须]
判据: The response identifies that the US tax treatment of the outbound IP transfer is governed by IRC Section 367(d).
提示: Correctly identifying Section 367(d) is essential as it governs outbound intangible transfers, ensuring accurate tax mechanics.
出处: prbench:5de6ea87151756dbb8d40455 | 话题: Taxation & Cross-Border Structuring

## FIN-0409 [负面]
判据: The response proposes a royalty rate below 10%.
提示: Risks IRS adjustments due to misalignment with margins.
出处: prbench:5de6ea87151756dbb8d40455 | 话题: Taxation & Cross-Border Structuring

## FIN-0410 [负面]
判据: For 351/361 outbound transfers of intangibles, the response applies 367(d) (annual deemed royalties) and does not characterize the transfer as a 367(a) lump-sum capital gain.
提示: Misapplying 367(a) leads to incorrect lump-sum tax treatment, derailing analysis.
出处: prbench:5de6ea87151756dbb8d40455 | 话题: Taxation & Cross-Border Structuring

## FIN-0411 [必须]
判据: When computing U.S. federal and California corporate tax together, the response uses the combined rate formula (federal + state − federal×state), e.g., 21% and 8.84% ⇒ ~27.98%, rather than a simple sum.
提示: Provides actionable tax numbers using current US rates for SF-based LLC.
出处: prbench:5de6ea87151756dbb8d40455 | 话题: Taxation & Cross-Border Structuring

## FIN-0412 [必须]
判据: The response states DEI offers a 5-10% tax rate.
提示: Reflects incentive terms for accurate ETR projections.
出处: prbench:5de6ea87151756dbb8d40455 | 话题: Taxation & Cross-Border Structuring

## FIN-0413 [建议]
判据: If citing Singapore’s digital-economy targets, the response uses accurate current Singapore targets or omits unsupported numeric goals (and does not attribute Malaysia’s 70% SME 2025 target to Singapore).
提示: Adds context to strengthen DEI application strategy.
出处: prbench:5de6ea87151756dbb8d40455 | 话题: Taxation & Cross-Border Structuring

## FIN-0414 [负面]
判据: The response calculates US tax using only the 21% federal rate.
提示: Understates tax liability significantly for an SF-based LLC.
出处: prbench:5de6ea87151756dbb8d40455 | 话题: Taxation & Cross-Border Structuring

## FIN-0415 [必须]
判据: The response correctly identifies that any unrealized profit made between the parent and subsidiary needs to be eliminated where that profit has not yet been realized outside of the group.
提示: This is key to include as this would lead to overstating group profits.
出处: prbench:5f10b48437b24cc3966b4581 | 话题: Accounting & Financial Statement Analysis

## FIN-0416 [必须]
判据: The response states that the assets and liabilities of the parent and subsidiary are added together.
提示: This is a key accounting detail to include.
出处: prbench:5f10b48437b24cc3966b4581 | 话题: Accounting & Financial Statement Analysis

## FIN-0417 [必须]
判据: The response identifies that the total investment in the joint venture is tested annually for impairment.
提示: Key to include as it is not depreciated or amortised.
出处: prbench:5f10b48437b24cc3966b4581 | 话题: Accounting & Financial Statement Analysis

## FIN-0418 [建议]
判据: The response states that Tangle plc must adjust the cost of the venturer's share of retained profits/losses of the joint venture for the current period.
提示: good explanation to include as to how to correctly consolidate the joint venture.
出处: prbench:5f10b48437b24cc3966b4581 | 话题: Accounting & Financial Statement Analysis

## FIN-0419 [必须]
判据: The response identifies that Tangle plc has significant influence over Grove Ltd.
提示: This is key and the main reason why equity method is applied.
出处: prbench:5f10b48437b24cc3966b4581 | 话题: Accounting & Financial Statement Analysis

## FIN-0420 [必须]
判据: The response includes how control of the subsidiary is reflected under IFRS (e.g., by including all of the subsidiary's assets, liabilities, income and expenses, even where the parent doesn't own 100% of the subsidiary).
提示: An important concept to explain.
出处: prbench:5f10b48437b24cc3966b4581 | 话题: Accounting & Financial Statement Analysis

## FIN-0421 [必须]
判据: The response states that Tangle plc must record the investment in a joint venture initially at cost.
提示: Important explanation as to how to correctly consolidate the joint venture.
出处: prbench:5f10b48437b24cc3966b4581 | 话题: Accounting & Financial Statement Analysis

## FIN-0422 [必须]
判据: The response correctly identifies that any intra-group transactions need to be eliminated between the parent and subsidiary.
提示: This is key to avoid double counting on the balance sheet.
出处: prbench:5f10b48437b24cc3966b4581 | 话题: Accounting & Financial Statement Analysis

## FIN-0423 [必须]
判据: The response states that Grove Ltd must be accounted for using the equity method.
提示: This is an important concept to mention.
出处: prbench:5f10b48437b24cc3966b4581 | 话题: Accounting & Financial Statement Analysis

## FIN-0424 [建议]
判据: The response refers to the 'single entity concept' in relation to the subsidiary.
提示: Only slightly important to mention.
出处: prbench:5f10b48437b24cc3966b4581 | 话题: Accounting & Financial Statement Analysis

## FIN-0425 [必须]
判据: The response states that ownership of the subsidiary is reflected via a non-controlling interest.
提示: A key concept to explain.
出处: prbench:5f10b48437b24cc3966b4581 | 话题: Accounting & Financial Statement Analysis

## FIN-0426 [必须]
判据: The response states that for the investment in the joint venture, no amortization is permitted.
提示: Key to include to ensure the user knows how to correctly account for the investment in subsequent years.
出处: prbench:5f10b48437b24cc3966b4581 | 话题: Accounting & Financial Statement Analysis

## FIN-0427 [建议]
判据: The response explains that because Tangle plc doesn't have control over Grove Ltd, complete consolidation would not be permitted under IFRS 11.
提示: This is an enhancement but not strictly required.
出处: prbench:5f10b48437b24cc3966b4581 | 话题: Accounting & Financial Statement Analysis

## FIN-0428 [建议]
判据: The response identifies that in the consolidated statement of financial position the investment in the joint venture is shown as a single line figure.
提示: Only slightly important but it does enhance the quality of the response.
出处: prbench:5f10b48437b24cc3966b4581 | 话题: Accounting & Financial Statement Analysis

## FIN-0429 [建议]
判据: The response clarifies that Walt Ltd is a subsidiary of Tangle plc.
提示: only slightly important as this doesn't need to specifically be mentioned as long as control and ownership are explained.
出处: prbench:5f10b48437b24cc3966b4581 | 话题: Accounting & Financial Statement Analysis

## FIN-0430 [建议]
判据: The response identifies that in the consolidated statement of P&L there is a single line for the venturer's share of the joint venture's results for that period.
提示: Only slightly important but it does enhance the response.
出处: prbench:5f10b48437b24cc3966b4581 | 话题: Accounting & Financial Statement Analysis

## FIN-0431 [必须]
判据: The response identifies that for the joint venture, goodwill is subsumed within the carrying amount of the joint venture in the consolidated statement of financial position.
提示: This is key to include so that the user knows not to try and separately account for goodwill.
出处: prbench:5f10b48437b24cc3966b4581 | 话题: Accounting & Financial Statement Analysis

## FIN-0432 [必须]
判据: The response computes the weighted average cost of capital (WACC) immediately after the proposed capital-structure transaction, explicitly showing inputs for the risk-free rate, beta, equity risk premium, tax rate, and pre-tax cost of debt.
提示: The computation itself verifies quantitative rigor and requires explicit parameter disclosure.
出处: prbench:5f667b8dfb36d5ff127cc4d9 | 话题: Corporate Finance

## FIN-0433 [必须]
判据: The response calculates rating metrics (e.g., ND/EBITDA, EBIT/Interest, and FFO/Net Debt using rating-agency definitions).
提示: Translates internal metrics to agency equivalents, ensuring comparability with rating triggers.
出处: prbench:5f667b8dfb36d5ff127cc4d9 | 话题: Corporate Finance

## FIN-0434 [必须]
判据: The response computes covenant headroom (i.e., leverage, interest-coverage, and restricted-payment limits from debt documents, showing numeric post-transaction headroom).
提示: Verifies compliance with contractual constraints, distinct from liquidity stress tests.
出处: prbench:5f667b8dfb36d5ff127cc4d9 | 话题: Corporate Finance

## FIN-0435 [必须]
判据: The response calculates the interest earned as approximately £1.36m (e.g., based on a compound interest formula and on the £30m, 18-month escrow).
提示: Demonstrates fundamental financial accuracy over simple interest.
出处: prbench:5fddb54637f1ccf6f74cb928 | 话题: Corporate Finance

## FIN-0436 [必须]
判据: The response calculates Path A2 (accept buyer's revised terms with increased £50m escrow indemnities)'s capped-indemnity net present value as approximately £174m to £175m.
提示: Establishes the value of the restructured escrow with bounded risk.
出处: prbench:5fddb54637f1ccf6f74cb928 | 话题: Corporate Finance

## FIN-0437 [建议]
判据: The response's calculation for Path C (litigation) deducts the £2m in upfront legal fees.
提示: Confirms a basic, explicit cost input is correctly applied.
出处: prbench:5fddb54637f1ccf6f74cb928 | 话题: Corporate Finance

## FIN-0438 [必须]
判据: The response's calculation for Path B applies a time-value of money discount to the £170m payment.
提示: Correctly applies fundamental time value of money principles.
出处: prbench:5fddb54637f1ccf6f74cb928 | 话题: Corporate Finance

## FIN-0439 [必须]
判据: The response calculates Path B (switch to competing bidder)'s final net present value as approximately £165m to £166m.
提示: Provides the key financial metric for the winning option.
出处: prbench:5fddb54637f1ccf6f74cb928 | 话题: Corporate Finance

## FIN-0440 [必须]
判据: The response provides a recommendation based on the risk-adjusted NPV (e.g., Path B "switch to competing bidder" has the optimal / highest risk-adjusted NPV).
提示: This is an explicit ask from prompt.
出处: prbench:5fddb54637f1ccf6f74cb928 | 话题: Corporate Finance

## FIN-0441 [必须]
判据: The response's calculation for Path B (switch to a competing bidder) deducts the value of the forgone £3m working capital uplift.
提示: Tests the crucial, expert-level insight of a hidden cost.
出处: prbench:5fddb54637f1ccf6f74cb928 | 话题: Corporate Finance

## FIN-0442 [必须]
判据: The response calculates Path A1 (accept buyer's revised terms without increased escrow)'s net present value as approximately £155m to £156m.
提示: Quantifies the baseline outcome for the price reduction path.
出处: prbench:5fddb54637f1ccf6f74cb928 | 话题: Corporate Finance

## FIN-0443 [必须]
判据: Response correctly identifies that the proposed receiver-payer swaption collar structure is inappropriate for hedging against rising rates, explicitly stating that receiver swaptions protect against falling rates, not rising rates.
提示: This is a fundamental directional error that would expose the client to exactly the risk they're trying to hedge. Receiver swaptions gain value when rates fall below the strike, providing no protection against the client's stated concern of a 200bp+ rate spike. Getting this direction wrong represents a catastrophic failure in derivatives structuring.
出处: prbench:61139c8c4221f9b8833aea88 | 话题: Derivatives & Structured Products

## FIN-0444 [必须]
判据: Response explains that selling receiver swaptions worsens the portfolio's existing negative convexity exposure because callable bonds already represent short receiver optionality.
提示: This demonstrates sophisticated understanding that callable bonds embed short receiver options, and selling additional receivers amplifies the negative convexity problem rather than solving it. This insight separates expert from novice analysis.
出处: prbench:61139c8c4221f9b8833aea88 | 话题: Derivatives & Structured Products

## FIN-0445 [负面]
判据: Response recommends a receiver-payer swaption collar where long receiver swaptions are the primary hedge component for protecting against rising rates.
提示: This represents a fundamental misunderstanding of swaption mechanics and creates a hedge that moves in the opposite direction to the client's risk. Receiver swaptions lose value when rates rise, providing no protection against the stated 200bp+ spike concern.
出处: prbench:61139c8c4221f9b8833aea88 | 话题: Derivatives & Structured Products

## FIN-0446 [必须]
判据: The response ensures metric weights explicitly sum to 100% (or 1.0) across all metrics included in the aggregate score.
提示: Ensuring weight normalization.
出处: prbench:61a2fa497c3f82e81981bce8 | 话题: Risk Management & Stress Testing

## FIN-0447 [必须]
判据: The response addresses redundancy/double-counting by noting highly correlated metrics.
提示: It is critical to handle redundancy/double-counting issues.
出处: prbench:61a2fa497c3f82e81981bce8 | 话题: Risk Management & Stress Testing

## FIN-0448 [必须]
判据: The response applies the standard EVE sensitivity formula: Change in EVE = -(Duration Gap) * EVE * Change in Y.
提示: This ensures the response uses the EVE formula correctly.
出处: prbench:61c1634ec1ab8608ada92092 | 话题: Risk Management & Stress Testing

## FIN-0449 [建议]
判据: The response clarifies that a bank with long fixed-rate mortgage assets has a duration gap of 7 years.
提示: This clarifies the duration gap in order to provide a reasonable estimate.
出处: prbench:61c1634ec1ab8608ada92092 | 话题: Risk Management & Stress Testing

## FIN-0450 [必须]
判据: The response performs the EVE change quantification accurately as: Change in EVE = -(7) * $500M * +0.0050 = -$17.5M.
提示: This correctly performs the EVE change calculation based on stated inputs.
出处: prbench:61c1634ec1ab8608ada92092 | 话题: Risk Management & Stress Testing

## FIN-0451 [必须]
判据: The response identifies the "severe" scenario for the described asset-liability structure as one in which steepening stress from short rates increases more than that from long rates.
提示: This answers the main explicit request from the prompt: identify the severe/worse case stress test scenario.
出处: prbench:61c1634ec1ab8608ada92092 | 话题: Risk Management & Stress Testing

## FIN-0452 [负面]
判据: The response acknowledges the importance of PVs in this scenario by incorporating PVs (e.g., PV assets, PV liabilities) into its EVE quantification analysis.
提示: PVs shouldn't be considered and are redundant in this scenario.
出处: prbench:61c1634ec1ab8608ada92092 | 话题: Risk Management & Stress Testing

## FIN-0453 [负面]
判据: The response includes the short-term rates (e.g., +400 bps short) in the EVE calculation.
提示: It's a big mistake to include the short-term rates, since the rise in short term rates exacerbates the economic loss through the NII squeeze, not impacting the immediate EVE calculation.
出处: prbench:61c1634ec1ab8608ada92092 | 话题: Risk Management & Stress Testing

## FIN-0454 [必须]
判据: The response uses the change in the rate applied to the assets (i.e., the long-term rate) as the "Change in Y" for the EVE calculation.
提示: This ensures the EVE quantification is accurate.
出处: prbench:61c1634ec1ab8608ada92092 | 话题: Risk Management & Stress Testing

## FIN-0455 [建议]
判据: The response integrates the combined effects of the shutdown with an anticipated Fed pivot (e.g., on equity valuation, by decomposing cash-flow impacts, and connecting to sector WACC and equity risk premia).
提示: This addresses the integrated assessment of combined effect prompt ask.
出处: prbench:62ea13bb25806538a0e7d3a8 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0456 [必须]
判据: The response concludes that a government shutdown could strengthen the demand for U.S. Treasuries since USTs reflect a global safe haven during times of volatility.
提示: Explicitly asked in the prompt.
出处: prbench:62ea13bb25806538a0e7d3a8 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0457 [必须]
判据: The response calculates inventory turnover as COGS/average inventory.
提示: Use of correct formulas is important
出处: prbench:634e823f4ac9719cee965d86 | 话题: Corporate Finance

## FIN-0458 [必须]
判据: The response calculates DSO to be 62 days.
提示: Accuracy of calculations is critically important
出处: prbench:634e823f4ac9719cee965d86 | 话题: Corporate Finance

## FIN-0459 [必须]
判据: The response calculates inventory turnover to be 0.5.
提示: Accuracy of calculations is critically important
出处: prbench:634e823f4ac9719cee965d86 | 话题: Corporate Finance

## FIN-0460 [必须]
判据: The response calculates DPO to be 10 days.
提示: Accuracy of calculations is critically important
出处: prbench:634e823f4ac9719cee965d86 | 话题: Corporate Finance

## FIN-0461 [必须]
判据: The response calculates DPO as Average A/P/COGS x number of days in the period.
提示: Use of correct formulas is important
出处: prbench:634e823f4ac9719cee965d86 | 话题: Corporate Finance

## FIN-0462 [必须]
判据: The response recognizes that a strong inventory turnover ratio is around 5.
提示: It is important to be able to measure performance against industry standard to get insight into if there is an issue or not
出处: prbench:634e823f4ac9719cee965d86 | 话题: Corporate Finance

## FIN-0463 [必须]
判据: The response calculates DSO as Average A/R/Total Credit Sales x Number of days in period.
提示: Use of correct formulas is important
出处: prbench:634e823f4ac9719cee965d86 | 话题: Corporate Finance

## FIN-0464 [必须]
判据: The response quantifies ladder rollover through six quarters and shows an even 4-year ladder adds to interest, reaching ~3.9% of EBITDA by Q6.
提示: This captures the dynamic build of interest costs.
出处: prbench:643796de687003869b5de46a | 话题: Corporate Finance

## FIN-0465 [必须]
判据: The response quantifies immediate floater pass through; it calculates the instant hit from 40% floating under +250 bps (e.g., 0.025 * 0.4 * 0.25 = 2.5% of EBITDA).
提示: This ensures the response sizes the shock on day one, it anchors materiality for cash planning.
出处: prbench:643796de687003869b5de46a | 话题: Corporate Finance

## FIN-0466 [必须]
判据: The response separates immediate from rolling effects; it explicitly distinguishes the floater hit now from refi glide up.
提示: It distinguish timing of impacts.
出处: prbench:643796de687003869b5de46a | 话题: Corporate Finance

## FIN-0467 [必须]
判据: The response states higher policy rates raise financing costs/WACC/hurdles.
提示: This criterion prevents fundamental errors.
出处: prbench:643796de687003869b5de46a | 话题: Corporate Finance

## FIN-0468 [必须]
判据: The response addresses what happens if the sale price to the IMF differs from the purchase price from Chile, for example, explaining that any difference would be recorded as a valuation change (holding gain or loss) in Australia's reserve assets within the International Investment Position (IIP), or noting that if the prices differ, this represents a change in the value of reserve asset holdings between the acquisition and disposal.
提示: Real-world transactions often involve price changes between purchase and sale. Addressing this scenario demonstrates sophisticated understanding and provides practical guidance for common variations.
出处: prbench:6460912c3ec6a1abd82a8917 | 话题: International Finance & FX Hedging

## FIN-0469 [建议]
判据: The response notes that the Chilean company is not a monetary institution (i.e., it is not a central bank or international financial institution).
提示: This distinction is important for understanding why the Chilean transaction is recorded differently from the IMF transaction - it provides helpful context beyond the core BoP mechanics.
出处: prbench:6460912c3ec6a1abd82a8917 | 话题: International Finance & FX Hedging

## FIN-0470 [负面]
判据: The response treats both the Chilean purchase and IMF sale as having the same or symmetrical balance of payments classification (e.g., describing both as "goods transactions" or both as "reserve asset transactions"), failing to recognize their fundamentally different treatments.
提示: Treating them symmetrically demonstrates fundamental misunderstanding of BoP classification principles.
出处: prbench:6460912c3ec6a1abd82a8917 | 话题: International Finance & FX Hedging

## FIN-0471 [必须]
判据: The response identifies the receipt of payment from the IMF as an increase in other reserve asset components (such as SDRs, reserve position in the IMF, or foreign currency holdings).
提示: Understanding that the payment increases other reserve assets (creating a recomposition within reserves rather than a net change) is essential for proper BoP recording of the complete transaction.
出处: prbench:6460912c3ec6a1abd82a8917 | 话题: International Finance & FX Hedging

## FIN-0472 [必须]
判据: The response identifies where these transactions would appear in standard BoP presentation tables, such as specifying that the goods import appears in the current account's goods line and the IMF transaction appears in the financial account's reserve assets section.
提示: Understanding where transactions appear in published BoP statistics helps practitioners find and verify these entries in actual statistical releases, making the guidance actionable.
出处: prbench:6460912c3ec6a1abd82a8917 | 话题: International Finance & FX Hedging

## FIN-0473 [必须]
判据: The response explains the impact of these transactions on key BoP metrics, such as noting that the Chilean purchase worsens the current account balance but doesn't affect the overall financial account balance.
提示: Understanding how individual transactions affect aggregate BoP indicators helps users interpret the broader economic significance and supports practical analysis.
出处: prbench:6460912c3ec6a1abd82a8917 | 话题: International Finance & FX Hedging

## FIN-0474 [负面]
判据: The response incorrectly states that the purchase of gold from the Chilean company immediately creates monetary gold or reserve assets for Australia, without recognizing that the gold remains non-monetary until the Reserve Bank monetizes it.
提示: This is a fundamental conceptual error. Gold purchased from a private company is non-monetary gold (a commodity) until a monetary authority designates it as part of official reserves.
出处: prbench:6460912c3ec6a1abd82a8917 | 话题: International Finance & FX Hedging

## FIN-0475 [建议]
判据: The response acknowledges timing considerations, such as noting that transactions should be recorded when economic ownership changes.
提示: The prompt doesn't specify exact timing, so a sophisticated response would acknowledge this ambiguity and clarify the timing principle used for recording under BPM6 accrual accounting.
出处: prbench:6460912c3ec6a1abd82a8917 | 话题: International Finance & FX Hedging

## FIN-0476 [必须]
判据: The response identifies the payment to Chile for the gold as a $100m AUD financial account credit (representing an outflow of Australian financial assets to pay for the import).
提示: In BoP accounting, a payment outflow is recorded as a credit in the financial account (decrease in Australian assets or increase in liabilities). This balances the current account debit from the goods import.
出处: prbench:6460912c3ec6a1abd82a8917 | 话题: International Finance & FX Hedging

## FIN-0477 [必须]
判据: The response explains why the Chilean transaction cannot be recorded in reserve assets despite being gold "for monetary reserves", for example, clarifying that the nature of the counterparty (non-monetary vs. monetary) determines classification, not the purchaser's intended use.
提示: This tests whether the response understands that BoP classification depends on the nature of parties involved and the type of gold (monetary vs. non-monetary), not on the purchaser's intentions. This nuance is frequently missed.
出处: prbench:6460912c3ec6a1abd82a8917 | 话题: International Finance & FX Hedging

## FIN-0478 [必须]
判据: The response identifies the purchase of gold from Chile as a $100m AUD goods import (debit in the current account of the balance of payments).
提示: This is the foundational BoP entry for this transaction - correctly identifying it as a current account goods import is essential for accurate balance of payments accounting.
出处: prbench:6460912c3ec6a1abd82a8917 | 话题: International Finance & FX Hedging

## FIN-0479 [必须]
判据: The response correctly identifies E-mini S&P 500 futures (CME) and SPX options (Cboe) as distinct instruments and includes both in the hedging toolkit along with VIX derivatives and Treasury futures.
提示: Tests accurate knowledge of derivative instruments and their trading venues, correcting terminology errors.
出处: prbench:651bdbd60885de8a45455e77 | 话题: Risk Management & Stress Testing

## FIN-0480 [必须]
判据: The response recommends Expected Shortfall (ES) alongside VaR for risk measurement, defining ES as the average loss in the worst X% of cases and explaining why ES better captures tail risk than VaR.
提示: Tests knowledge of coherent risk measures and modern risk management best practices beyond basic VaR.
出处: prbench:651bdbd60885de8a45455e77 | 话题: Risk Management & Stress Testing

## FIN-0481 [必须]
判据: The response correctly lists all 11 GICS sectors for industry exposure limits: Energy, Materials, Industrials, Consumer Discretionary, Consumer Staples, Health Care, Financials, Information Technology, Communication Services, Utilities, and Real Estate.
提示: Tests accurate knowledge of standard industry classification systems used in portfolio risk management.
出处: prbench:651bdbd60885de8a45455e77 | 话题: Risk Management & Stress Testing

## FIN-0482 [必须]
判据: The response correctly defines Marginal VaR as the partial derivative ∂VaR_p/∂w_i and Component VaR as w_i × MVaR_i, distinguishing these concepts from standalone manager VaR calculations.
提示: Tests precise understanding of portfolio risk decomposition mathematics, correcting the conflated definitions in the original rubric
出处: prbench:651bdbd60885de8a45455e77 | 话题: Risk Management & Stress Testing

## FIN-0483 [必须]
判据: The response states that Component VaRs sum to total portfolio VaR under Euler's theorem (Σ CVaR_i = VaR_p), but clarifies that this additivity property does not apply to standalone VaR or Expected Shortfall measures.
提示: Tests sophisticated knowledge of when risk measures are and are not additive, a fundamental concept often misunderstood.
出处: prbench:651bdbd60885de8a45455e77 | 话题: Risk Management & Stress Testing

## FIN-0484 [必须]
判据: The response notes that traditional VAR measures such as parametric VAR are not additive at the portfolio level. E.g., VAR(A + B) ≠ VAR(A) + VAR(B).
提示: this is why we are going to introduce other measures.
出处: prbench:651bdbd60885de8a45455e77 | 话题: Risk Management & Stress Testing

## FIN-0485 [必须]
判据: The response explains market-structure factors as a mechanism for ETF swings, e.g., by showing how ETFs that only hold a sample of their index or use tracking methods can experience sharper intraday swings than the full basket of securities.
提示: explanantion of the mechanis behind the user ask
出处: prbench:6538d6eb7e2646437d980a46 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0486 [必须]
判据: The response directly explains why an ETF can swing more than its constituent stocks, e.g., by linking the phenomenon to specific mechanisms such as liquidity mismatches, intraday pricing, concentration or sampling effects.
提示: Answering the core question of the user.
出处: prbench:6538d6eb7e2646437d980a46 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0487 [必须]
判据: The response states that short-term deviations between ETFs and their underlying stocks are normal.
提示: Non-experts want reassurance; the response must close the loop on their doubt.
出处: prbench:6538d6eb7e2646437d980a46 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0488 [必须]
判据: The response explains liquidity mismatches as a mechanism for ETF swings, e.g., by showing how bond ETFs can trade more actively and transparently than the underlying bonds, so in stressed markets, their prices may fall below NAV because the bonds themselves are harder to sell quickly.
提示: Explanation of the mechanism behind the user's ask
出处: prbench:6538d6eb7e2646437d980a46 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0489 [必须]
判据: The response's application of its chosen normalisation convention is consistent for the EBITDA metric.
提示: Demonstrating consistency for the denominator of the multiple is a key test of the response's logical integrity.
出处: prbench:658f4e6ced1099a34e62937c | 话题: Accounting & Financial Statement Analysis

## FIN-0490 [必须]
判据: The response explains that under IFRS 16, Enterprise Value is inflated because the lease liability is added to the calculation.
提示: This is the second half of the core conceptual problem.
出处: prbench:658f4e6ced1099a34e62937c | 话题: Accounting & Financial Statement Analysis

## FIN-0491 [必须]
判据: The response explicitly warns that the $400m undiscounted lease commitment figure is not an annual rent expense.
提示: This is a critical clarifying point that prevents a common and significant error in the analysis.
出处: prbench:658f4e6ced1099a34e62937c | 话题: Accounting & Financial Statement Analysis

## FIN-0492 [建议]
判据: The response correctly states that finance (or capital) leases should be excluded from the operating lease adjustments.
提示: Technical nuance that ensures the normalisation is applied only to the items that are actually different between the standards.
出处: prbench:658f4e6ced1099a34e62937c | 话题: Accounting & Financial Statement Analysis

## FIN-0493 [负面]
判据: The response incorrectly adds a rent expense back to the reported EBITDA of the IFRS 16 company.
提示: This is a fundamental double-counting error.
出处: prbench:658f4e6ced1099a34e62937c | 话题: Accounting & Financial Statement Analysis

## FIN-0494 [必须]
判据: The response's application of its chosen normalisation convention is consistent for the Enterprise Value metric.
提示: Demonstrating consistency for the numerator of the multiple is a key test of the response's logical integrity.
出处: prbench:658f4e6ced1099a34e62937c | 话题: Accounting & Financial Statement Analysis

## FIN-0495 [必须]
判据: The response explains that under IFRS 16, reported EBITDA is inflated because rent expense is moved below the EBITDA line.
提示: This is the first half of the core conceptual problem.
出处: prbench:658f4e6ced1099a34e62937c | 话题: Accounting & Financial Statement Analysis

## FIN-0496 [必须]
判据: The response selects one of the two valid normalisation conventions (either adjusting the IFRS 16 filer down or adjusting the peers up).
提示: Choosing a single, clear convention is the most critical step that governs the entire normalisation workflow.
出处: prbench:658f4e6ced1099a34e62937c | 话题: Accounting & Financial Statement Analysis

## FIN-0497 [必须]
判据: The response's application of its chosen normalisation convention is consistent for the leverage metric.
提示: Demonstrating consistency for the leverage ratio completes the application of the chosen methodology across all required metrics.
出处: prbench:658f4e6ced1099a34e62937c | 话题: Accounting & Financial Statement Analysis

## FIN-0498 [必须]
判据: States that a NAV facility does not automatically crystallize carry.
提示: Stops erroneous carry booking from financing moves.
出处: prbench:65d468e394e79f321dae6c3c | 话题: Alternative Investments & Private Markets

## FIN-0499 [必须]
判据: States that a continuation vehicle does not automatically crystallize carry.
提示: Avoids false carry recognition on restructuring.
出处: prbench:65d468e394e79f321dae6c3c | 话题: Alternative Investments & Private Markets

## FIN-0500 [必须]
判据: Carry crystallizes only when proceeds are distributed to LPs under a European waterfall.
提示: Prevents misstating GLP economics.
出处: prbench:65d468e394e79f321dae6c3c | 话题: Alternative Investments & Private Markets

## FIN-0501 [负面]
判据: The response contains incorrect calculations of accruals according to GAAP or IFRS standards (e.g., failing to distinguish between operating and investing accruals, incorrectly calculating total accruals as net income minus operating cash flow, or misclassifying non-cash items in the accrual calculation).
提示: Penalises fundamental errors in accounting calculations that would invalidate the analysis.
出处: prbench:661813f9dc9c82246ea1a9bd | 话题: Investment Strategy & Portfolio Design

## FIN-0502 [必须]
判据: The response discusses how to adjust accounting metrics for industry-specific factors (e.g., excluding financial firms when using debt-based metrics, normalising capital expenditure for utilities and energy companies, or using industry-relative percentile ranks rather than absolute values).
提示: Tests understanding of cross-sectional comparability in accounting data.
出处: prbench:661813f9dc9c82246ea1a9bd | 话题: Investment Strategy & Portfolio Design

## FIN-0503 [必须]
判据: The response identifies accounting-based indicators that specifically isolate the size factor from other confounding factors (e.g., size-adjusted accrual ratios, small-cap-specific earnings surprise metrics, or relative financial strength indicators comparing small vs. large firms).
提示: Tests sophisticated understanding of factor isolation in accounting metrics.
出处: prbench:661813f9dc9c82246ea1a9bd | 话题: Investment Strategy & Portfolio Design

## FIN-0504 [负面]
判据: The response contains incorrect interpretations of what accrual metrics indicate about earnings quality (e.g., claiming high accruals always indicate earnings manipulation, stating that all accruals reverse in the subsequent quarter, or asserting that accruals have the same implications across all industries regardless of business model).
提示: Penalises fundamental errors in understanding what accounting metrics actually measure.
出处: prbench:661813f9dc9c82246ea1a9bd | 话题: Investment Strategy & Portfolio Design

## FIN-0505 [必须]
判据: The response states that under US GAAP, Bitcoin is classified as an intangible asset with an indefinite useful life.
提示: potential risk
出处: prbench:66a191c86d4b98d2932c1a8e | 话题: FinTech, Crypto & Digital Assets

## FIN-0506 [必须]
判据: The response states that under US GAAP, Bitcoin cannot be revalued upward to fair market value and may only be written down when impaired below its cost.
提示: potential risk
出处: prbench:66a191c86d4b98d2932c1a8e | 话题: FinTech, Crypto & Digital Assets

## FIN-0507 [必须]
判据: The response identifies that limited supply does not always equate to high demand as a critical flaw in the argument that MSTR can only become more valuable.
提示: This is a core instruction-following rubric.
出处: prbench:66a191c86d4b98d2932c1a8e | 话题: FinTech, Crypto & Digital Assets

## FIN-0508 [负面]
判据: The response attributes MicroStrategy’s valuation changes solely to operational performance.
提示: ignoring the impact of BTC prove movements.
出处: prbench:66a191c86d4b98d2932c1a8e | 话题: FinTech, Crypto & Digital Assets

## FIN-0509 [必须]
判据: The response identifies the persistent gap between lower cash flow from operations and higher net income as a significant red flag.
提示: Recurring divergence suggests earning quality issues.
出处: prbench:66c931189c14af088b2e8a82 | 话题: Accounting & Financial Statement Analysis

## FIN-0510 [必须]
判据: The response identifies the significant increase in Days Sales Outstanding (DSO) from 45 to 78 days as a red flag for receivables quality.
提示: Indicates slower customer payments.
出处: prbench:66c931189c14af088b2e8a82 | 话题: Accounting & Financial Statement Analysis

## FIN-0511 [必须]
判据: The response checks for consistency (e.g., stable cash conversion ratio, CFO growth matching revenue growth) between the reported revenue growth and the growth in cash flow.
提示: If does not match, growth may not be real.
出处: prbench:66c931189c14af088b2e8a82 | 话题: Accounting & Financial Statement Analysis

## FIN-0512 [必须]
判据: The response explains that modern revenue recognition standards (e.g., IFRS 15/ASC 606) are based on the principle of transferring control of goods or services.
提示: This tests precise knowledge of IFRS 15
出处: prbench:66c931189c14af088b2e8a82 | 话题: Accounting & Financial Statement Analysis

## FIN-0513 [必须]
判据: The response connects the 300-bps gross margin compression to potential issues like rising costs or pricing pressure, despite revenue growth.
提示: Indicates cost management issues.
出处: prbench:66c931189c14af088b2e8a82 | 话题: Accounting & Financial Statement Analysis

## FIN-0514 [必须]
判据: The response explicitly states assets pledged to the central bank cannot also be counted as available liquid assets.
提示: Checks if the response knows that you cannot count the same security twice, that pledged assets must be removed from HQLA.
出处: prbench:66e28dec73f0b6d13e8c0e48 | 话题: Risk Management & Stress Testing

## FIN-0515 [必须]
判据: The response clearly defines the daily USD funding gap by stating that the daily funding gap equals cash inflows minus cash outflows after funding actions.
提示: Checks for clear metric definition.
出处: prbench:66e28dec73f0b6d13e8c0e48 | 话题: Risk Management & Stress Testing

## FIN-0516 [必须]
判据: The response explicitly states central bank collateral margins are separate from dealer repo haircuts.
提示: central bank margins differ from repo haircuts.
出处: prbench:66e28dec73f0b6d13e8c0e48 | 话题: Risk Management & Stress Testing

## FIN-0517 [必须]
判据: The response includes control variables such as VIX, interest rates, or inflation in the regression model.
提示: Ensures the index’s effect is isolated from standard macro factors.
出处: prbench:673dd60966858eef344b7ae5 | 话题: Investment Strategy & Portfolio Design

## FIN-0518 [必须]
判据: The response compares the EV/EBITDA with EV/FCF multiples of the peer set, such as comparing EV/EBITDA with EV/FCF multiples before and after synergy, providing clear definitions of FCF.
提示: Directly addresses prompt requirement for "comparison of EV/EBITDA and EV/FCF multiples versus peers (both pre- and post-synergy)" which was missing from original rubrics. Critical for relative valuation methodology in M&A analysis.
出处: prbench:677fd6df82bfc1c45f5fbc39 | 话题: Corporate Finance

## FIN-0519 [必须]
判据: Quantifies annual leakage delta (€ difference) between SG and NL for ≥2 country-mix scenarios (e.g., equal split vs. Vietnam-heavy).
提示: Turns qualitative risk into actionable, comparable metrics.
出处: prbench:68c14bf5d7f95b2f67fb3c5d | 话题: Taxation & Cross-Border Structuring

## FIN-0520 [必须]
判据: Confirms French participation-exemption math (95% exempt; 5% taxed at 25% = 1.25%).
提示: Quantitative anchor for FR layer
出处: prbench:68c14bf5d7f95b2f67fb3c5d | 话题: Taxation & Cross-Border Structuring

## FIN-0521 [必须]
判据: Computes the Netherlands' total leakage (in € and %) with stepwise breakdown (Asia→NL, NL tax, NL→FR, French residual).
提示: Requires proper 95% participation math; few models show it.
出处: prbench:68c14bf5d7f95b2f67fb3c5d | 话题: Taxation & Cross-Border Structuring

## FIN-0522 [必须]
判据: Computes Singapore's total leakage (in € and %) with stepwise breakdown (Asia→SG, SG tax, SG→FR, French residual).
提示: Central quantitative check; incomplete in most answers.
出处: prbench:68c14bf5d7f95b2f67fb3c5d | 话题: Taxation & Cross-Border Structuring

## FIN-0523 [必须]
判据: The response identifies that the $20mm amortisation payment will put significant pressure on the company's tight cash position.
提示: Identifying the liquidity squeeze is key to the problem.
出处: prbench:6c23419a281c9f7888a7feb1 | 话题: Corporate Finance

## FIN-0524 [必须]
判据: The response explains the 0.2x leverage gap by stating that the company needs to either reduce net debt by 0.2x EBITDA or increase EBITDA by approximately 5%.
提示: Demonstrates a quantitative, foundational understanding of the problem, moving beyond qualitative description.
出处: prbench:6c23419a281c9f7888a7feb1 | 话题: Corporate Finance

## FIN-0525 [必须]
判据: The response explains that the $20mm amortisation payment does not change net debt if it is funded with cash on hand.
提示: Correctly defining net debt mechanics is a crucial concept.
出处: prbench:6c23419a281c9f7888a7feb1 | 话题: Corporate Finance

## FIN-0526 [必须]
判据: The response correctly states that the issuance of new secured debt does not, by itself, constitute a subordination of the existing unsecured bonds under the 2014 ISDA Definitions.
提示: This addresses a common misconception about subordination in the context of CDS.
出处: prbench:6d1a8a4016cc2e9189a96b32 | 话题: Derivatives & Structured Products

## FIN-0527 [必须]
判据: The response explains that the bond-CDS basis (CDS spread minus bond spread) can become more negative because the bond price falls due to priming from the new secured debt, while the CDS spread widens less because a trigger is now less likely.
提示: This tests the ability to explain the decoupling of bond and CDS prices.
出处: prbench:6d1a8a4016cc2e9189a96b32 | 话题: Derivatives & Structured Products

## FIN-0528 [必须]
判据: The response correctly explains that for a Restructuring to be triggered, there must be a deterioration in the creditworthiness of the reference entity.
提示: This tests a core condition for a Restructuring credit event.
出处: prbench:6d1a8a4016cc2e9189a96b32 | 话题: Derivatives & Structured Products

## FIN-0529 [必须]
判据: The response correctly explains that maturity limits under Modified Restructuring (MR) or Modified-Modified Restructuring (MMR) are deliverable obligation characteristics and do not prevent a Restructuring credit event from occurring.
提示: This corrects a common factual error about the role of maturity limits.
出处: prbench:6d1a8a4016cc2e9189a96b32 | 话题: Derivatives & Structured Products

## FIN-0530 [必须]
判据: The response correctly identifies that a voluntary, non-binding exchange offer does not trigger a Restructuring credit event under the 2014 ISDA Definitions because it does not alter the terms of the original bonds for non-participating holders.
提示: This is the most fundamental reason why many distressed exchanges do not trigger CDS.
出处: prbench:6d1a8a4016cc2e9189a96b32 | 话题: Derivatives & Structured Products

## FIN-0531 [必须]
判据: The response correctly identifies that a Restructuring credit event requires the satisfaction of the Multiple Holder Obligation, meaning the restructured obligation must be an obligation of the reference entity held by more than three holders.
提示: This tests knowledge of a key technical requirement for Restructuring.
出处: prbench:6d1a8a4016cc2e9189a96b32 | 话题: Derivatives & Structured Products

## FIN-0532 [必须]
判据: The response correctly identifies that the new secured debt primes the existing unsecured bonds, reducing their expected recovery in a default scenario.
提示: This tests the understanding of the credit impact of the exchange.
出处: prbench:6d1a8a4016cc2e9189a96b32 | 话题: Derivatives & Structured Products

## FIN-0533 [必须]
判据: The response correctly states that the Default Requirement (a notional materiality threshold) does not apply to the Restructuring credit event under the 2014 ISDA Definitions.
提示: This corrects another common factual error about the conditions for a Restructuring trigger.
出处: prbench:6d1a8a4016cc2e9189a96b32 | 话题: Derivatives & Structured Products

## FIN-0534 [必须]
判据: The response identifies that cross-currency MTM reporting requires a quanto adjustment when EUR cash flows are valued in CAD for mark-to-market purposes.
提示: Identifies need for quanto in cross-currency context. First step of recognition.
出处: prbench:6dee86e28e47bf31ad380cc0 | 话题: International Finance & FX Hedging

## FIN-0535 [必须]
判据: The response explains that barrier option valuation requires adjustments beyond standard Black-Scholes, such as barrier-adjusted formulas or reflection principle methods, due to the knock-out feature.
提示: Tests understanding that barriers require specialised pricing. Technical depth requirement.
出处: prbench:6dee86e28e47bf31ad380cc0 | 话题: International Finance & FX Hedging

## FIN-0536 [必须]
判据: The response correctly defines the range forward as a barrier option structure (such as a knock-out collar or double barrier option).
提示: Core definitional requirement from prompt. Tests understanding of structured product.
出处: prbench:6dee86e28e47bf31ad380cc0 | 话题: International Finance & FX Hedging

## FIN-0537 [必须]
判据: The response identifies the barrier type as knock-out barriers.
提示: Barrier monitoring is fundamental to accurate pricing.
出处: prbench:6dee86e28e47bf31ad380cc0 | 话题: International Finance & FX Hedging

## FIN-0538 [必须]
判据: The response incorporates the contract's path-dependency into the MTM calculation by adjusting the valuation based on whether the barriers have been historically breached.
提示: Path-dependent valuation fundamental to barrier options.
出处: prbench:6dee86e28e47bf31ad380cc0 | 话题: International Finance & FX Hedging

## FIN-0539 [必须]
判据: The response calculates Potential Future Exposure (PFE) at a specified confidence level such as the 95th or 99th percentile.
提示: Probabilistic quantification. Core deliverable.
出处: prbench:6dee86e28e47bf31ad380cc0 | 话题: International Finance & FX Hedging

## FIN-0540 [必须]
判据: The response explains how barrier proximity affects gamma, noting that gamma spikes near barrier levels.
提示: Barrier proximity creates nonlinear Greeks behaviour.
出处: prbench:6dee86e28e47bf31ad380cc0 | 话题: International Finance & FX Hedging

## FIN-0541 [必须]
判据: The response calculates or explains the barrier survival probability - the likelihood that EUR/CAD remains within 1.50-1.55 throughout the contract life.
提示: Integrates output into real-world control cycle.
出处: prbench:6dee86e28e47bf31ad380cc0 | 话题: International Finance & FX Hedging

## FIN-0542 [必须]
判据: The response identifies that volatility smile calibration for out-of-the-money barrier options uses market-quoted instruments such as 25-delta risk reversals (measuring skew) or butterfly spreads (measuring curvature/kurtosis).
提示: Market-standard vol surface calibration.
出处: prbench:6dee86e28e47bf31ad380cc0 | 话题: International Finance & FX Hedging

## FIN-0543 [必须]
判据: The response identifies that implied volatility skew or smile affects barrier option pricing differently than it affects at-the-money options.
提示: Material pricing impact (5-15%). Expert knowledge.
出处: prbench:6dee86e28e47bf31ad380cc0 | 话题: International Finance & FX Hedging

## FIN-0544 [必须]
判据: The response applies an appropriate barrier option valuation method such as closed-form barrier option pricing, binomial trees, or Monte Carlo simulation.
提示: Core to prompt's complaint, tests technical method selection.
出处: prbench:6dee86e28e47bf31ad380cc0 | 话题: International Finance & FX Hedging

## FIN-0545 [必须]
判据: The response identifies that knocked-out barrier options require Monte Carlo simulation for accurate exposure profile modelling.
提示: Discontinuity at barriers makes analytical solutions insufficient for exposure profiles.
出处: prbench:6dee86e28e47bf31ad380cc0 | 话题: International Finance & FX Hedging

## FIN-0546 [必须]
判据: The response defines conditional exposure as the exposure measurement given that barriers have not been breached to date (conditional on survival).
提示: Conditional exposure is standard risk metric for path-dependent derivatives.
出处: prbench:6dee86e28e47bf31ad380cc0 | 话题: International Finance & FX Hedging

## FIN-0547 [必须]
判据: The response defines unconditional exposure as the probability-weighted exposure across all possible barrier-touch scenarios, not conditional on current survival status.
提示: Unconditional exposure for comprehensive risk assessment.
出处: prbench:6dee86e28e47bf31ad380cc0 | 话题: International Finance & FX Hedging

## FIN-0548 [必须]
判据: The response states that the quanto adjustment incorporates the correlation between the EUR/CAD exchange rate and the interest rate differential as a key pricing component.
提示: Identifies need for quanto in cross-currency context. First step of recognition.
出处: prbench:6dee86e28e47bf31ad380cc0 | 话题: International Finance & FX Hedging

## FIN-0549 [负面]
判据: The response states the MTM losses are aligned with the actual cash flow (e.g., cash flow drain from collateral).
提示: The MTM losses on the hedge and the actual cash flow from drain from CIP violation and collateral are different, and has to be distinguished to avoid critical mistake.
出处: prbench:6e43da4709d5678b0d6638e6 | 话题: Risk Management & Stress Testing

## FIN-0550 [必须]
判据: The response correctly defines a reverse stress test as working backwards from a predetermined catastrophic outcome to identify its causes.
提示: Accurately define the reverse stress test is a critical point in answering the prompt.
出处: prbench:6e43da4709d5678b0d6638e6 | 话题: Risk Management & Stress Testing

## FIN-0551 [必须]
判据: The response interprets the sustainability calculation (e.g., a coverage ratio of 2.5x indicates dividends are well covered by FCF and sustainable).
提示: It discusses sustainability conceptually (mentions payout ratio/caveats) but does not compute FCF coverage or show the arithmetic needed to judge whether a payout is sustainable.
出处: prbench:6e7166ec94e8c39f2af853d4 | 话题: Corporate Finance

## FIN-0552 [必须]
判据: The response computes the payout ratio for a provided example using the formula Payout ratio = Dividend per share ÷ Earnings per share.
提示: The response shows the dividend percent change (30%) but does not compute payout ratio or state an EPS assumption; therefore it omits the concrete metric investors use to judge sustainability.
出处: prbench:6e7166ec94e8c39f2af853d4 | 话题: Corporate Finance

## FIN-0553 [必须]
判据: The response characterizes ACA premium credits as a sliding phase-out rather than a $120k statutory cliff.
提示: Incorrect “cliff” framing leads to the wrong optimization.
出处: prbench:6e78dd5193c63a469e72c4ef | 话题: Wealth Management, Financial Planning & Advice

## FIN-0554 [必须]
判据: The response computes the single-stock sale gain as $750k using the $150k basis for $900K holdings.
提示: Correct mechanics avoid mixing rate buckets and mis-pricing NIIT/IRMAA exposure.
出处: prbench:6e78dd5193c63a469e72c4ef | 话题: Wealth Management, Financial Planning & Advice

## FIN-0555 [必须]
判据: The response acknowledges that IRMAA is a delayed penalty (i.e., showing that the 2-year lookback affects 2026/2027).
提示: IRMAA is a delayed penalty; correct timing changes the choice.
出处: prbench:6e78dd5193c63a469e72c4ef | 话题: Wealth Management, Financial Planning & Advice

## FIN-0556 [必须]
判据: The response decomposes the NUA distribution into $120k ordinary income (basis) plus $480k LTCG (NUA amount) at the sale.
提示: Correct mechanics avoid mixing rate buckets and mis-pricing NIIT/IRMAA exposure.
出处: prbench:6e78dd5193c63a469e72c4ef | 话题: Wealth Management, Financial Planning & Advice

## FIN-0557 [必须]
判据: The response computes NIIT when the NUA path MAGI exceeds the $250k MFJ threshold as 3.8% on investment income over the threshold.
提示: Keeps the analysis comparable and decision-oriented per the prompt.
出处: prbench:6e78dd5193c63a469e72c4ef | 话题: Wealth Management, Financial Planning & Advice

## FIN-0558 [必须]
判据: The response states that NUA treatment requires a lump-sum distribution of the entire qualified plan in the triggering year.
提示: NUA eligibility / timing is the hinge of the decision; mis-stating it flips the conclusion.
出处: prbench:6e78dd5193c63a469e72c4ef | 话题: Wealth Management, Financial Planning & Advice

## FIN-0559 [负面]
判据: Response confuses permanent impact (order's footprint) with market trend (beta/exogenous price movement).
提示: Penalise bad judgment
出处: prbench:70666a55b21ddb48de74e555 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0560 [建议]
判据: Response identifies the arrival price as the benchmark price at the start of the parent order.
提示: Good to have, required but obvious
出处: prbench:70666a55b21ddb48de74e555 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0561 [负面]
判据: The response applies at least one named statistical model (e.g., regressions, AR(1) models, difference-in-differences) to quantitatively separate temporary from permanent market impact.
提示: Ensures response not just mentions but applies the statistical methodology for both impact types.
出处: prbench:70666a55b21ddb48de74e555 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0562 [必须]
判据: The response defines the temporary impact cost using the formula: Sign (Trade direction) * (Average Execution Price - Post-trade benchmark price).
提示: This ensures the formula accurately attributes temporary impact for both buys and sells.
出处: prbench:70666a55b21ddb48de74e555 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0563 [建议]
判据: The response defines the temporary impact as the component of trading cost expected to partially reverse after the order is complete.
提示: Reasoning for temporary impact
出处: prbench:70666a55b21ddb48de74e555 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0564 [必须]
判据: The response quantifies the amount of excess cash flow that would be trapped under the cash sweep (e.g., 75% of excess cash flow if leverage stays above 4.0x).
提示: Calculating the trapped cash amount is essential to understanding the amendment option's constraint.
出处: prbench:71f35bd4f8b67d86c59c4f2f | 话题: Corporate Finance

## FIN-0565 [必须]
判据: The response compares the $412M bond buyback cost to the $39M refinancing cost to conclude that buying back bonds is economically prohibitive.
提示: The comparison directly addresses the prompt's question about whether to buy back bonds and demonstrates why it's not viable.
出处: prbench:71f35bd4f8b67d86c59c4f2f | 话题: Corporate Finance

## FIN-0566 [必须]
判据: The response calculates the all-in cost of the refinancing option as $39M upfront ($31M make-whole + $8M unamortized fees) plus the net interest savings (from L+375 vs L+425) over the loan term.
提示: Essential to compare both options on equal footing.
出处: prbench:71f35bd4f8b67d86c59c4f2f | 话题: Corporate Finance

## FIN-0567 [必须]
判据: The response calculates the all-in cost of the amendment option as the 1% fee ($7.5M) plus the spread increase (L+425 vs L+275 = 150 bps higher) over the remaining loan term.
提示: Core financial comparison required to answer the prompt's central question.
出处: prbench:71f35bd4f8b67d86c59c4f2f | 话题: Corporate Finance

## FIN-0568 [负面]
判据: The response states that LIBOR + 425 bps is cheaper than LIBOR + 375 bps.
提示: A basic error that inverts the fundamental trade-off.
出处: prbench:71f35bd4f8b67d86c59c4f2f | 话题: Corporate Finance

## FIN-0569 [负面]
判据: The response confuses the springing cash sweep (i.e., excess cash flow diversion) with a mandatory prepayment from specific events like asset sales.
提示: Misunderstanding the cash sweep mechanism leads to incorrect impact assessment.
出处: prbench:71f35bd4f8b67d86c59c4f2f | 话题: Corporate Finance

## FIN-0570 [负面]
判据: The response claims the pari passu clause would not be triggered even though the new $850M facility clearly exceeds the $100M secured debt threshold.
提示: Ignoring a covenant violation could lead to catastrophic legal and financial consequences.
出处: prbench:71f35bd4f8b67d86c59c4f2f | 话题: Corporate Finance

## FIN-0571 [负面]
判据: The response calculates interest cost using simple interest instead of discounting cash flows to compare options on a present-value basis.
提示: Ignoring time value produces inaccurate comparisons.
出处: prbench:71f35bd4f8b67d86c59c4f2f | 话题: Corporate Finance

## FIN-0572 [建议]
判据: The response notes that the amendment fee is 1% of $750M = $7.5M.
提示: Accurate inputs are essential for valid conclusions.
出处: prbench:71f35bd4f8b67d86c59c4f2f | 话题: Corporate Finance

## FIN-0573 [必须]
判据: The response explains that a make-whole premium is compensation to lenders for lost future interest payments from early prepayment.
提示: Defining the concept helps users understand the $31M cost component.
出处: prbench:71f35bd4f8b67d86c59c4f2f | 话题: Corporate Finance

## FIN-0574 [必须]
判据: The response explains that the $8M in unamortized fees represents original loan costs that would be written off immediately upon refinancing (e.g., it creates a one-time accounting loss).
提示: Helps users understand the accounting treatment of the refinancing.
出处: prbench:71f35bd4f8b67d86c59c4f2f | 话题: Corporate Finance

## FIN-0575 [必须]
判据: The response presents both options' impact on enterprise value by comparing the NPV of lost growth CapEx under the amendment versus the upfront $39M cost plus interest savings under refinancing.
提示: Enterprise value maximization is the ultimate decision criterion.
出处: prbench:71f35bd4f8b67d86c59c4f2f | 话题: Corporate Finance

## FIN-0576 [必须]
判据: The response calculates the bond buyback cost at 103 as $400M × 103% = $412M.
提示: Accurate calculation of the buyback cost is needed to evaluate this alternative.
出处: prbench:71f35bd4f8b67d86c59c4f2f | 话题: Corporate Finance

## FIN-0577 [必须]
判据: The response estimates the value impact of foregone growth CapEx due to the cash sweep restriction (e.g., projected excess cash flow amounts, expected ROI/ROIC of growth CapEx).
提示: Understanding the opportunity cost of restricted growth investment informs the strategic decision.
出处: prbench:71f35bd4f8b67d86c59c4f2f | 话题: Corporate Finance

## FIN-0578 [必须]
判据: The response accurately determines grantor vs non-grantor status of each trust and explains tax consequences that drive planning choices post-2026.
提示: Fundamental trust taxation analysis for post-exemption planning.
出处: prbench:72b854b4c31f018435cb6461 | 话题: Taxation & Cross-Border Structuring

## FIN-0579 [必须]
判据: The response correctly calculates gross leverage as 5.3x by dividing $480m by $90m of EBITDA.
提示: Gross leverage is a key underwriting metric. An incorrect calculation fundamentally misrepresents the company's risk profile.
出处: prbench:74f96b4e9c6782c0c369802b | 话题: Corporate Finance

## FIN-0580 [必须]
判据: The response states that a successful refinancing plus a cash paydown would likely preserve equity.
提示: This is a key insight that contrasts with a restructuring, directly addressing the user's core concern.
出处: prbench:74f96b4e9c6782c0c369802b | 话题: Corporate Finance

## FIN-0581 [必须]
判据: The response explicitly states the total debt is $480m.
提示: A foundational error in calculating the debt stack invalidates all subsequent analysis of leverage and feasibility.
出处: prbench:74f96b4e9c6782c0c369802b | 话题: Corporate Finance

## FIN-0582 [必须]
判据: The response states net debt correctly as $330m.
提示: Undermines the entire analysis and demonstrates a failure to understand basic financial concepts.
出处: prbench:74f96b4e9c6782c0c369802b | 话题: Corporate Finance

## FIN-0583 [必须]
判据: The response states that stress testing assesses the resilience of financial institutions under adverse scenarios.
提示: gives important summary of stress testing
出处: prbench:74fc341eeeb5a83d66c61299 | 话题: Risk Management & Stress Testing

## FIN-0584 [建议]
判据: The response explicitly calculates the $110M net funding gap ($150M capex minus $40M available cash).
提示: Clarifies external financing requirement
出处: prbench:75d605b5d514b647e586e0ad | 话题: Corporate Finance

## FIN-0585 [必须]
判据: The response explicitly states that 5.13x leverage would breach the 4x EBITDA/net debt covenant.
提示: Key constraint identification
出处: prbench:75d605b5d514b647e586e0ad | 话题: Corporate Finance

## FIN-0586 [必须]
判据: The response calculates projected dilution for the equity option using the formula: dilution % = new shares issued / (existing shares + new shares).
提示: Provides clear financing structure recommendation
出处: prbench:75d605b5d514b647e586e0ad | 话题: Corporate Finance

## FIN-0587 [必须]
判据: The response calculates that funding the entire $150M expansion with debt would result in $410M net debt.
提示: Critical for understanding financing constraints
出处: prbench:75d605b5d514b647e586e0ad | 话题: Corporate Finance

## FIN-0588 [必须]
判据: The response calculates the maximum additional debt that could be raised while maintaining 4x covenant compliance.
提示: Essential for determining viable debt capacity
出处: prbench:75d605b5d514b647e586e0ad | 话题: Corporate Finance

## FIN-0589 [必须]
判据: The response calculates the company's starting net debt as $260M ($300M TLB minus $40M cash).
提示: Foundational calculation for analyzing options
出处: prbench:75d605b5d514b647e586e0ad | 话题: Corporate Finance

## FIN-0590 [必须]
判据: The response calculates available liquidity before project funding, including both cash and undrawn revolver.
提示: Tests the initial resources
出处: prbench:75d605b5d514b647e586e0ad | 话题: Corporate Finance

## FIN-0591 [必须]
判据: The response calculates projected dilution for the equity option: Dilution % = new shares issued / (existing shares + new shares).
提示: Isolates shareholder impact; objective, checkable number.
出处: prbench:75d605b5d514b647e586e0ad | 话题: Corporate Finance

## FIN-0592 [必须]
判据: The response quantifies the resulting covenant headroom in the downside scenario by calculating the difference between the 4x covenant limit and the projected leverage ratio (e.g., at $72M EBITDA, the 4x limit allows $288M net debt, providing $28M headroom).
提示: Provides concrete risk assessment for decision-making
出处: prbench:75d605b5d514b647e586e0ad | 话题: Corporate Finance

## FIN-0593 [必须]
判据: The response calculates the company's starting leverage ratio as 3.25x ($260M net debt divided by $80M EBITDA).
提示: Essential baseline for covenant compliance analysis
出处: prbench:75d605b5d514b647e586e0ad | 话题: Corporate Finance

## FIN-0594 [负面]
判据: The response presents leverage calculations only for the state after financing but before using cash for the project.
提示: Fundamental misunderstanding of covenant analysis
出处: prbench:75d605b5d514b647e586e0ad | 话题: Corporate Finance

## FIN-0595 [必须]
判据: The response calculates the minimum equity required to fund the capex project while maintaining covenant compliance, using the actual formula Net Debt = Debt – Cash and the covenant limit Net Debt/EBITDA ≤ 4.0x.
提示: Essential for understanding equity requirements
出处: prbench:75d605b5d514b647e586e0ad | 话题: Corporate Finance

## FIN-0596 [必须]
判据: The response explains that in the absence of a Permanent Establishment (PE), business profits are not taxable in India under the treaty.
提示: Important alternative outcome that affects overall tax strategy.
出处: prbench:791ec34a9eced568662d3f94 | 话题: Taxation & Cross-Border Structuring

## FIN-0597 [必须]
判据: The response correctly explains the interaction between tax exposures, noting that the characterisation of income as FTS or royalties under the treaty takes precedence over its classification as business profits.
提示: Professional analysis showing understanding of complex tax law interactions.
出处: prbench:791ec34a9eced568662d3f94 | 话题: Taxation & Cross-Border Structuring

## FIN-0598 [必须]
判据: The response correctly states that the equalisation levy is no longer an applicable tax for current revenue streams.
提示: Critical current law update.
出处: prbench:791ec34a9eced568662d3f94 | 话题: Taxation & Cross-Border Structuring

## FIN-0599 [必须]
判据: The response explains that the key test for FTS under the UK-India treaty is whether services 'make available' technical knowledge or skill to the Indian customer.
提示: Critical treaty interpretation that determines tax liability.
出处: prbench:791ec34a9eced568662d3f94 | 话题: Taxation & Cross-Border Structuring

## FIN-0600 [必须]
判据: The response states that FTS/royalties trigger withholding tax at 10-15% under the UK-India treaty.
提示: Specific tax rate impacts cash flow and pricing decisions.
出处: prbench:791ec34a9eced568662d3f94 | 话题: Taxation & Cross-Border Structuring

## FIN-0601 [必须]
判据: The response recommends using the company's current capital structure (mostly equity and convertible debt) for the WACC calculation.
提示: This is a fundamental error in valuation theory. It penalizes the inclusion of advice that would lead to a systematically incorrect valuation.
出处: prbench:79fe82a6a3cb418c9f861182 | 话题: Corporate Finance

## FIN-0602 [必须]
判据: The response explicitly advises using a target capital structure, not the company's current capital structure, for the WACC calculation.
提示: This is a critical, non-negotiable point in any forward-looking DCF valuation. Using the current, likely suboptimal capital structure of a pre-profitability company is a fundamental error.
出处: prbench:79fe82a6a3cb418c9f861182 | 话题: Corporate Finance

## FIN-0603 [负面]
判据: The response's DCF methodology is based on a single, blended revenue growth rate assumption for the entire explicit forecast period.
提示: This penalizes the inclusion of a specific, simplistic, and inaccurate modeling approach. Using a single blended rate for a company with a dynamic business mix is a fundamental error that leads to a flawed valuation.
出处: prbench:79fe82a6a3cb418c9f861182 | 话题: Corporate Finance

## FIN-0604 [负面]
判据: The response presents the Perpetuity Growth and Exit Multiple methods as equally valid or interchangeable approaches for this specific company's terminal value calculation.
提示: This penalizes the inclusion of non-committal, "textbook" advice. Presenting both methods as equally valid is actively unhelpful and demonstrates a failure to provide the expert judgment requested in the prompt.
出处: prbench:79fe82a6a3cb418c9f861182 | 话题: Corporate Finance

## FIN-0605 [必须]
判据: When discussing the Exit Multiple Method, the response recommends using a forward EV/revenue multiple and justifies why it is more appropriate for a high-growth, pre-profitability software company than an EV/EBITDA multiple.
提示: This tests for deep, sector-specific valuation expertise. For a company that is still burning cash but has strong revenue growth and gross margins, EV/Revenue is the standard valuation metric. An expert must not only state this but also explain why an EBITDA multiple would be misleading or inappropriate at this stage of the company's lifecycle.
出处: prbench:79fe82a6a3cb418c9f861182 | 话题: Corporate Finance

## FIN-0606 [必须]
判据: The response correctly identifies that the 12-14% Cost of Equity is likely driven by a high beta selected from a volatile peer group or the application of a size premium (e.g., Fama-French).
提示: This demonstrates a deeper, more nuanced understanding of the CAPM model and its practical application, showing the ability to diagnose why a number might seem counterintuitive.
出处: prbench:79fe82a6a3cb418c9f861182 | 话题: Corporate Finance

## FIN-0607 [必须]
判据: The response says to buy USD calls or TWD puts if the company earns in TWD and pays costs in USD.
提示: checks if the response hedges currency risk correctly part 2
出处: prbench:7b38fece340edd280686e461 | 话题: International Finance & FX Hedging

## FIN-0608 [必须]
判据: The response explicitly states that cross-currency swaps hedge multi-period debt interest and principal.
提示: Checks if the response use the right instruments.
出处: prbench:7b38fece340edd280686e461 | 话题: International Finance & FX Hedging

## FIN-0609 [必须]
判据: The response states that changes in value for a cash flow hedge are recorded in "other comprehensive income" first.
提示: Checks if response explains where cash flow hedge changes go at first.
出处: prbench:7b38fece340edd280686e461 | 话题: International Finance & FX Hedging

## FIN-0610 [必须]
判据: The response explicitly states that USD/TWD non-deliverable forwards or standard forwards hedge forecast operating cash flows.
提示: checks to see if the response use the right instrument.
出处: prbench:7b38fece340edd280686e461 | 话题: International Finance & FX Hedging

## FIN-0611 [必须]
判据: The response states that one should buy USD puts or TWD calls if the company earns in USD and pays costs in TWD.
提示: checks if the response hedges currency risk correctly
出处: prbench:7b38fece340edd280686e461 | 话题: International Finance & FX Hedging

## FIN-0612 [必须]
判据: The response states cash flow hedge amounts in other comprehensive income move to profit and loss when the related sales/costs happen.
提示: Checks if response explains when cash flow hedge amount move into profit and loss
出处: prbench:7b38fece340edd280686e461 | 话题: International Finance & FX Hedging

## FIN-0613 [必须]
判据: The response states that if the company earns in TWD and pays costs in USD, a stronger USD would hurt the company.
提示: checks if response explains which currency move would hurt the company.
出处: prbench:7b38fece340edd280686e461 | 话题: International Finance & FX Hedging

## FIN-0614 [必须]
判据: The response states if the company earns in USD and pays costs in TWD, a weaker USD would hurt the company.
提示: checks if response explains which currency move would hurt the company.
出处: prbench:7b38fece340edd280686e461 | 话题: International Finance & FX Hedging

## FIN-0615 [建议]
判据: The response selects a put option, rather than a call option, when calculating the net sterling receipt from the OTC options.
提示: This is key as a call option is not appropriate in these circumstances.
出处: prbench:7cc2481918e238aab618f892 | 话题: International Finance & FX Hedging

## FIN-0616 [必须]
判据: The response selects the discount rate of 0.2265 for calculating the forward rate.
提示: If this is incorrect, the final net sterling receipt figure will also be incorrect.
出处: prbench:7cc2481918e238aab618f892 | 话题: International Finance & FX Hedging

## FIN-0617 [必须]
判据: The response calculates the net sterling receipt from the options as approximately £2,085,145.
提示: This is the correct sterling receipt figure for using the put option.
出处: prbench:7cc2481918e238aab618f892 | 话题: International Finance & FX Hedging

## FIN-0618 [必须]
判据: The response calculates the net forward sterling receipt as approximately 2,084,938.
提示: This is the correct net sterling receipt figure for using the forward contract.
出处: prbench:7cc2481918e238aab618f892 | 话题: International Finance & FX Hedging

## FIN-0619 [必须]
判据: The response adds the discount rate of 0.2265 to the spot rate of 95.4930 to calculate the forward rate of 95.7195.
提示: If this is incorrect, the final net sterling receipt figure will also be incorrect.
出处: prbench:7cc2481918e238aab618f892 | 话题: International Finance & FX Hedging

## FIN-0620 [必须]
判据: The response calculates the gross forward sterling receipt as approximately £2,089,438.
提示: This is the correct sterling receipt figure for using the forward contract.
出处: prbench:7cc2481918e238aab618f892 | 话题: International Finance & FX Hedging

## FIN-0621 [必须]
判据: The response selects the spot rate of 95.4930 when calculating the forward rate.
提示: If this is incorrect, the final net sterling receipt figure will also be incorrect.
出处: prbench:7cc2481918e238aab618f892 | 话题: International Finance & FX Hedging

## FIN-0622 [必须]
判据: The response calculates the gross sterling receipt from the options as approximately £2,093,145.
提示: This is the correct sterling receipt figure for using the put option.
出处: prbench:7cc2481918e238aab618f892 | 话题: International Finance & FX Hedging

## FIN-0623 [必须]
判据: The response specifies the covenant threshold for net debt-to-EBITDA as 3.75× (e.g., providing the figure within the text for verification).
提示: Confirms covenant covenant
出处: prbench:7e516d7465b0b75dda5586e4 | 话题: Corporate Finance

## FIN-0624 [必须]
判据: The response quantifies post-transaction leverage under a 70 percent take-up scenario (e.g., using £244 million net debt and £70 million EBITDA, giving an expected ratio near 3.5×).
提示: Tests downside leverage
出处: prbench:7e516d7465b0b75dda5586e4 | 话题: Corporate Finance

## FIN-0625 [必须]
判据: The response specifies the covenant threshold for interest coverage as 3.0× (e.g., by providing the figure within the text for verification).
提示: Confirms coverage covenant
出处: prbench:7e516d7465b0b75dda5586e4 | 话题: Corporate Finance

## FIN-0626 [必须]
判据: The response calculates post-transaction leverage as net debt divided by EBITDA.
提示: Measures base leverage
出处: prbench:7e516d7465b0b75dda5586e4 | 话题: Corporate Finance

## FIN-0627 [必须]
判据: The response estimates post-transaction liquidity by adding starting cash (£45 million) to net proceeds under each take-up case (e.g., 90%, 70%, 50% take-up).
提示: Validates liquidity outcome
出处: prbench:7e516d7465b0b75dda5586e4 | 话题: Corporate Finance

## FIN-0628 [必须]
判据: The response calculates covenant headroom by subtracting post-transaction leverage from the stated covenant threshold.
提示: Quantifies covenant buffer
出处: prbench:7e516d7465b0b75dda5586e4 | 话题: Corporate Finance

## FIN-0629 [必须]
判据: The response identifies the DXY (e.g., the US dollar index) as a key driver of the international gold price.
提示: This criterion checks that the response includes a key driver of the international gold price, as the latter is priced in US dollars in the international markets
出处: prbench:7f409b9386e87497c0c626c8 | 话题: Alternative Investments & Private Markets

## FIN-0630 [负面]
判据: The response stacks together two arguably independent drivers of the gold price into a single one (e.g., real interest rates and the US dollar).
提示: This criterion checks that the response follows the instruction by identifying two (separate) key drivers, rather than stacking them up (e.g., real interest rates and the US dollar are stand-alone drivers of the gold price)
出处: prbench:7f409b9386e87497c0c626c8 | 话题: Alternative Investments & Private Markets

## FIN-0631 [必须]
判据: The response distinguishes between HFT effects on different order sizes, noting that small retail orders typically benefit from tighter spreads while large institutional orders face higher execution costs or slippage.
提示: How HFT creates a tiered market, impacting different participants in different ways.
出处: prbench:80e9d60b24c96f93c487c667 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0632 [必须]
判据: The response states that high-frequency trading generally narrows bid-ask spreads under normal market conditions.
提示: The primary and most widely cited benefit of HFT.
出处: prbench:80e9d60b24c96f93c487c667 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0633 [必须]
判据: Identifies that longer-maturity bonds (20-year and 30-year) experience greater yield increases compared to shorter maturities during dollar weakness scenarios.
提示: It is part of the prompt request to analyze the spread across yields of different maturities.
出处: prbench:81c86ada1e229b3a614268c9 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0634 [建议]
判据: Reports Expected Shortfall (ES) in ratio points, e.g., “ES = 0.05 means a 5 pp CET1 decline.”
提示: Ratio units inform capital ratios directly.
出处: prbench:8263d078ee0cb0e6e83f4d41 | 话题: Risk Management & Stress Testing

## FIN-0635 [必须]
判据: Uses the Basel IRB capital function for RWA (K(PD,LGD,ρ); RWA = 12.5×K×EAD).
提示: Denominator realism is decisive for CET1 tails.
出处: prbench:8263d078ee0cb0e6e83f4d41 | 话题: Risk Management & Stress Testing

## FIN-0636 [必须]
判据: Computes 3-year Expected Shortfall on capital loss (ΔCET1), not on the CET1 level.
提示: ES must apply to losses to reflect risk magnitude.
出处: prbench:8263d078ee0cb0e6e83f4d41 | 话题: Risk Management & Stress Testing

## FIN-0637 [必须]
判据: Reports ES in euros.
提示: Monetary units enable planning and shortfall funding logic.
出处: prbench:8263d078ee0cb0e6e83f4d41 | 话题: Risk Management & Stress Testing

## FIN-0638 [必须]
判据: The response explicitly specifies the structure of the macro variable covariance matrix as D (diag( volatilities)) .R.D (correlation matrix).
提示: Ensures coherent shock generation and valid simulation.
出处: prbench:8263d078ee0cb0e6e83f4d41 | 话题: Risk Management & Stress Testing

## FIN-0639 [必须]
判据: Computes and reports the macro-space tail probability (p_macro) of the severe scenario, distinct from the capital-space probability.
提示: Captures the rarity of the macroeconomic path itself
出处: prbench:8263d078ee0cb0e6e83f4d41 | 话题: Risk Management & Stress Testing

## FIN-0640 [必须]
判据: The response calculates or estimates the expected total transaction costs using industry-standard formulas (such as implementation shortfall = market impact + timing risk + fees, with specific basis point estimates for each component).
提示: Professional execution analysis requires quantitative cost estimation.
出处: prbench:83186c31b41caf228998e8a8 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0641 [必须]
判据: The response discusses mathematical market impact models (such as the square root law, where impact ∝ √(order size/volume)) with parameter considerations for mid-cap stocks.
提示: Professional execution modeling requires knowledge of empirically-calibrated impact coefficients.
出处: prbench:83186c31b41caf228998e8a8 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0642 [负面]
判据: The response suggests aggressive market orders or immediate execution as a solution to minimize market impact.
提示: Aggressive execution would dramatically worsen market impact for a 4x ADV trade, representing fundamentally incorrect advice.
出处: prbench:83186c31b41caf228998e8a8 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0643 [负面]
判据: The response claims that tight bid-ask spreads (5 bps) guarantee low market impact regardless of order size or market depth.
提示: This demonstrates misunderstanding of the relationship between spreads, depth, and market impact, contradicting the depth issues described in the prompt
出处: prbench:83186c31b41caf228998e8a8 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0644 [必须]
判据: The response quantifies the DSO cash tie-up from a ten-day increase as approximately £11.2 million.
提示: Confirms correct working capital arithmetic.
出处: prbench:84015da6578bce554b765edd | 话题: Risk Management & Stress Testing

## FIN-0645 [必须]
判据: The response calculates the incremental interest cost from a fifty-basis-point rate increase on £110 million debt as about £0.55 million per year.
提示: Calculates the incremental interest
出处: prbench:84015da6578bce554b765edd | 话题: Risk Management & Stress Testing

## FIN-0646 [必须]
判据: The response states the compounded revenue run rate of approximately £410 million after a ten percent and a five percent sequential drop.
提示: Verifies correct compounding of demand shocks.
出处: prbench:84015da6578bce554b765edd | 话题: Risk Management & Stress Testing

## FIN-0647 [必须]
判据: The response defines “mean–variance optimization instability” as the joint problem of sensitivity to expected return estimates and covariance matrix estimation error.
提示: Ensures the model gives a precise technical definition of instability, covering both critical sources of error.
出处: prbench:8481888ab71fac9263c119e2 | 话题: Investment Strategy & Portfolio Design

## FIN-0648 [必须]
判据: The response states the countercyclical buffer is not a tax on loans.
提示: checks for another basic policy mistake.
出处: prbench:84b3c4801652b147f4d563ce | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0649 [必须]
判据: The response explains that higher capital requirements (countercyclical buffer) raise banks’ cost of lending, causing a modest shift of borrowers to shadow lenders.
提示: checks for accuracy for the core ask.
出处: prbench:84b3c4801652b147f4d563ce | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0650 [必须]
判据: The response states the countercyclical buffer is not a cash/liquidity reserve.
提示: checks for basic policy mistakes.
出处: prbench:84b3c4801652b147f4d563ce | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-0651 [必须]
判据: The response explicitly raises the required return for illiquidity.
提示: Core ask of the prompt.
出处: prbench:8513b84566332e1bfc4440c7 | 话题: Alternative Investments & Private Markets

## FIN-0652 [负面]
判据: The response claims American waterfalls delay LP net DPI more than European waterfalls.
提示: Technical error leading to wrong cash timing.
出处: prbench:8513b84566332e1bfc4440c7 | 话题: Alternative Investments & Private Markets

## FIN-0653 [必须]
判据: The response acknowledges the late-vintage J curve (calls high, DPI low) (e.g., it notes front-loaded calls and minimal early distributions).
提示: Matches real PE cash flow shape.
出处: prbench:8513b84566332e1bfc4440c7 | 话题: Alternative Investments & Private Markets

## FIN-0654 [建议]
判据: The response provides a plausible capital call rate band for late-vintage funds during the stress period (e.g., '20-30% of commitments called annually in years 1-3, vs. normal 15-25%').
提示: Grounds pacing in realistic call cadence.
出处: prbench:8513b84566332e1bfc4440c7 | 话题: Alternative Investments & Private Markets

## FIN-0655 [必须]
判据: The response correctly calculates that the £40m order represents 80% of the ADV per day.
提示: This core calculation frames the entire execution problem and is essential for justifying the chosen strategy.
出处: prbench:85b28cf6338a28ac1149198e | 话题: Market Microstructure, Trading & Liquidity

## FIN-0656 [负面]
判据: The response makes a material mathematical error in its pre-trade analysis (e.g., the ADV calculation).
提示: A fundamental mathematical error means the entire analysis is useless.
出处: prbench:85b28cf6338a28ac1149198e | 话题: Market Microstructure, Trading & Liquidity

## FIN-0657 [必须]
判据: The response indicates that paying taxes in the UK does not mean you cannot be a tax resident in Ghana.
提示: This is explicit ask from prompt and is vital information needed to clarify users confusion.
出处: prbench:888818bc091f6c2c9a23a1e4 | 话题: Taxation & Cross-Border Structuring

## FIN-0658 [负面]
判据: The response suggests that the user can switch from a student visa to a work visa to improve tax residency.
提示: Tax residency is not determined by visa status.
出处: prbench:888818bc091f6c2c9a23a1e4 | 话题: Taxation & Cross-Border Structuring

## FIN-0659 [必须]
判据: The response mentions that the tax residency in the UK is determined by the Statutory Residence Test.
提示: This provides needed information to the user.
出处: prbench:888818bc091f6c2c9a23a1e4 | 话题: Taxation & Cross-Border Structuring

## FIN-0660 [必须]
判据: The response mentions that immigration or visa status does not determine tax residency in the UK.
提示: This clarifies any user confusion.
出处: prbench:888818bc091f6c2c9a23a1e4 | 话题: Taxation & Cross-Border Structuring

## FIN-0661 [必须]
判据: The response mentions that there is a difference between paying taxes in a country and being a tax resident in that country (e.g., paying taxes does not determine tax residency).
提示: This sets the premise to clarify the users confusion.
出处: prbench:888818bc091f6c2c9a23a1e4 | 话题: Taxation & Cross-Border Structuring

## FIN-0662 [负面]
判据: The response mentions that you are no longer a tax resident in Ghana.
提示: This is incorrect since the user might still have permanent home ties in Ghana.
出处: prbench:888818bc091f6c2c9a23a1e4 | 话题: Taxation & Cross-Border Structuring

## FIN-0663 [必须]
判据: The response mentions that the user is likely still considered a tax resident of Ghana due to the permanent home ties policy.
提示: This is a reason for still remaining a tax resident of Gh.
出处: prbench:888818bc091f6c2c9a23a1e4 | 话题: Taxation & Cross-Border Structuring

## FIN-0664 [必须]
判据: The response indicates the two rules that apply to international students to determine tax residency (i.e., the 183-day rule and the Sufficient Ties Test) if the 183-day rule is not met.
提示: This is vital information to the user.
出处: prbench:888818bc091f6c2c9a23a1e4 | 话题: Taxation & Cross-Border Structuring

## FIN-0665 [必须]
判据: The response correctly concludes that syndicated loan covenants are generally stricter than those found in bond indentures.
提示: Tests for the core comparative analysis of covenants.
出处: prbench:8909acde8631a6924e6c121b | 话题: Corporate Finance

## FIN-0666 [必须]
判据: The response identifies that both options will decrease interest coverage ratios, such as the EBITDA / Interest Expense ratio.
提示: Tests for the primary impact on solvency analysis.
出处: prbench:8909acde8631a6924e6c121b | 话题: Corporate Finance

## FIN-0667 [必须]
判据: The response correctly distinguishes the public, tradeable nature of corporate bonds from the private, relationship-based nature of syndicated loans.
提示: Tests for the fundamental product distinction.
出处: prbench:8909acde8631a6924e6c121b | 话题: Corporate Finance

## FIN-0668 [负面]
判据: The response states that bond covenants are generally stricter than syndicated loan covenants.
提示: Penalises a fundamental misunderstanding of debt products.
出处: prbench:8909acde8631a6924e6c121b | 话题: Corporate Finance

## FIN-0669 [必须]
判据: The response identifies that both options will increase key leverage ratios, such as Debt-to-Equity or Net Debt-to-EBITDA.
提示: Tests for the primary impact on leverage analysis.
出处: prbench:8909acde8631a6924e6c121b | 话题: Corporate Finance

## FIN-0670 [必须]
判据: The response explains that both options increase long-term debt and cash on the balance sheet.
提示: Tests for the core balance sheet impact.
出处: prbench:8909acde8631a6924e6c121b | 话题: Corporate Finance

## FIN-0671 [必须]
判据: The response proposes a recalculated hard IRR that excludes recallable cash flows.
提示: Shows ability to adjust IRR correctly.
出处: prbench:8b1626cca821a6d9e14c3a91 | 话题: Alternative Investments & Private Markets

## FIN-0672 [必须]
判据: The response recognises that hard DPI only counts non-recallable distributions.
提示: Distinguishes true cash returned; advanced LP focus.
出处: prbench:8b1626cca821a6d9e14c3a91 | 话题: Alternative Investments & Private Markets

## FIN-0673 [必须]
判据: The response states that carry should only be charged on true profits.
提示: Core safeguard; ensures LP-GP alignment.
出处: prbench:8b1626cca821a6d9e14c3a91 | 话题: Alternative Investments & Private Markets

## FIN-0674 [必须]
判据: The response defines soft DPI as recallable distributions ÷ paid-in capital.
提示: Separates temporary cash flows from permanent ones.
出处: prbench:8b1626cca821a6d9e14c3a91 | 话题: Alternative Investments & Private Markets

## FIN-0675 [必须]
判据: The response states explicitly that recallable distributions are not realized returns.
提示: Core insight; without it the answer misses the main flaw in reported IRR.
出处: prbench:8b1626cca821a6d9e14c3a91 | 话题: Alternative Investments & Private Markets

## FIN-0676 [必须]
判据: The response explains the fundamental economic mechanism of life settlement investments—specifically that returns are generated when actual mortality exceeds life expectancy estimates, making longevity risk (the risk that insured lives live longer than projected) the primary driver of portfolio underperformance—before presenting technical modeling steps.
提示: tests for explanations.
出处: prbench:8b60c8e102e7c3de18de346f | 话题: Risk Management & Stress Testing

## FIN-0677 [必须]
判据: The response states that total cash flows for each policy for each simulation run consist of the cost basis, the monthly premium payments until the simulated time of death, and the policy death benefit received at the simulated time of death.
提示: The portfolio consists of life insurance policies, so all the cash flows associated with ownership of a life insurance policy must be used when calculating the IRR of ownership.
出处: prbench:8b60c8e102e7c3de18de346f | 话题: Risk Management & Stress Testing

## FIN-0678 [必须]
判据: The response acknowledges that it is the guaranteed minimum return embedded in the WLI contract that is the driver of the low risk profile of this investment.
提示: really important, this is why the semi std deviation is so low.
出处: prbench:8b67e1a37ba0d2836e6a0523 | 话题: Investment Strategy & Portfolio Design

## FIN-0679 [必须]
判据: The response recognizes that in most years the dividend paid into the WLI policy exceeds the minimum return, e.g., the policy's guaranteed minimum crediting rate.
提示: Why the model works.
出处: prbench:8b67e1a37ba0d2836e6a0523 | 话题: Investment Strategy & Portfolio Design

## FIN-0680 [必须]
判据: The response states that a WLI Company has never failed to pay the guaranteed minimum credit to the insured.
提示: credit experience
出处: prbench:8b67e1a37ba0d2836e6a0523 | 话题: Investment Strategy & Portfolio Design

## FIN-0681 [必须]
判据: The response states that a WLI Company effectively pays a dividend based upon the following formula: Investment Return - Investment Costs - Mortality Expense.
提示: how it works at the ins company level.
出处: prbench:8b67e1a37ba0d2836e6a0523 | 话题: Investment Strategy & Portfolio Design

## FIN-0682 [必须]
判据: The response explains that the expected return of a portfolio is a weighted sum of the expected returns of each asset times the asset weight in the portfolio.
提示: This is how it works.
出处: prbench:8b67e1a37ba0d2836e6a0523 | 话题: Investment Strategy & Portfolio Design

## FIN-0683 [必须]
判据: The response explains that the Maximum Sharpe Ratio portfolio is not simply composed of the assets with the highest Sharpe Ratios, e.g., in our 3-asset portfolio, neither the Long-Term Corporate Bonds nor the WLI contract is amongst the assets with the 3 largest Sharpe ratios.
提示: an observation worth making.
出处: prbench:8b67e1a37ba0d2836e6a0523 | 话题: Investment Strategy & Portfolio Design

## FIN-0684 [必须]
判据: The response recognizes that the returns on a WLI contract are free of tax in the accumulation phase, rendering it very attractive for consideration on an after-tax basis.
提示: very important
出处: prbench:8b67e1a37ba0d2836e6a0523 | 话题: Investment Strategy & Portfolio Design

## FIN-0685 [必须]
判据: The response states that historically, the high commissions associated with WLI have made it an inefficient asset due to its initial losses when considered in a mean-variance framework.
提示: Prior to institutional pricing on life insurance the product was too expensive
出处: prbench:8b67e1a37ba0d2836e6a0523 | 话题: Investment Strategy & Portfolio Design

## FIN-0686 [必须]
判据: The response states that the maximum Sharpe ratio portfolio included an allocation of 40.87% to WLI.
提示: Helpful for the rest of the discussion.
出处: prbench:8b67e1a37ba0d2836e6a0523 | 话题: Investment Strategy & Portfolio Design

## FIN-0687 [必须]
判据: The response explains that the correlations provided for the WLI insurance contract versus the other assets are extremely low (in some cases negative), e.g., |rho| < 0.1.
提示: Important for all mean-std deviation exercies.
出处: prbench:8b67e1a37ba0d2836e6a0523 | 话题: Investment Strategy & Portfolio Design

## FIN-0688 [必须]
判据: The response clarifies that the portfolio standard deviation is dependent upon the correlations calculated for the pool of assets.
提示: crtical reason for WLI working as an asset.
出处: prbench:8b67e1a37ba0d2836e6a0523 | 话题: Investment Strategy & Portfolio Design

## FIN-0689 [必须]
判据: The response states that for the pre-CGT portion of the property (acquired in 1978), the beneficiaries' cost basis is established as the market value at the date of death.
提示: tests knowledge of the corresponding, but different, cost base rule for pre-CGT assets.
出处: prbench:8bc0e33dfe6d1e628047d68e | 话题: Wealth Management, Financial Planning & Advice

## FIN-0690 [负面]
判据: The response states that the 2007 amalgamation of the property titles was a CGT event.
提示: This is a crucial safety check. Mistaking an administrative process (title amalgamation) for a taxable event is a significant factual error that would lead to fundamentally incorrect advice and is unacceptable in a response.
出处: prbench:8bc0e33dfe6d1e628047d68e | 话题: Wealth Management, Financial Planning & Advice

## FIN-0691 [必须]
判据: The response identifies that the portion of the property acquired in 1978 is CGT-exempt.
提示: This tests the ability to apply the legal rule from criterion #1 to the specific facts of the case.
出处: prbench:8bc0e33dfe6d1e628047d68e | 话题: Wealth Management, Financial Planning & Advice

## FIN-0692 [必须]
判据: The response states that a 50% CGT discount is available for post-CGT assets held by an individual for more than 12 months.
提示: assesses knowledge of a key tax-reduction mechanism in Australia. Identifying the availability of the 50% discount is essential for calculating the true tax impact on the portfolio.
出处: prbench:8bc0e33dfe6d1e628047d68e | 话题: Wealth Management, Financial Planning & Advice

## FIN-0693 [必须]
判据: The response explains that selling assets within the estate triggers an immediate CGT liability.
提示: evaluates the response's ability to explain the strategic options available.
出处: prbench:8bc0e33dfe6d1e628047d68e | 话题: Wealth Management, Financial Planning & Advice

## FIN-0694 [必须]
判据: The response states that for post-CGT assets (the tech stocks and 2007 land), beneficiaries inherit the deceased's original cost basis upon death.
提示: checks for understanding of a crucial aspect of inheritance tax law.
出处: prbench:8bc0e33dfe6d1e628047d68e | 话题: Wealth Management, Financial Planning & Advice

## FIN-0695 [负面]
判据: The response suggests the goal is to disburse the pre-tax value equally, rather than the post-tax value.
提示: tests for a core conceptual misunderstanding of the client's goal.
出处: prbench:8bc0e33dfe6d1e628047d68e | 话题: Wealth Management, Financial Planning & Advice

## FIN-0696 [必须]
判据: The response states that assets acquired in Australia before 20 September 1985 are generally exempt from Capital Gains Tax (CGT).
提示: Verifies that the response is grounded in the foundational legal principle governing the entire scenario.
出处: prbench:8bc0e33dfe6d1e628047d68e | 话题: Wealth Management, Financial Planning & Advice

## FIN-0697 [必须]
判据: The response identifies that the land acquired in 2007 is subject to CGT.
提示: Important for any downstream logic.
出处: prbench:8bc0e33dfe6d1e628047d68e | 话题: Wealth Management, Financial Planning & Advice

## FIN-0698 [必须]
判据: The response calculates the taxable capital gain on the tech stocks as $100,000, based on a $200,000 total gain and the 50% CGT discount.
提示: tests the practical application of the CGT discount rule. A high-quality response must not only state the theory but also accurately perform the calculation to quantify the financial outcome for the client.
出处: prbench:8bc0e33dfe6d1e628047d68e | 话题: Wealth Management, Financial Planning & Advice

## FIN-0699 [必须]
判据: Must state that ON RRP near zero forces MMFs to reallocate cash into Treasury bills or repo markets.
提示: Linking liquidity drain to reallocation behavior.
出处: prbench:8c4a212c39a9ef81c48b6881 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0700 [建议]
判据: State that sponsored repo volumes surged from around $500 billion in 2019 to around $2 trillion in 2024.
提示: Historical volume insight.
出处: prbench:8c4a212c39a9ef81c48b6881 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0701 [必须]
判据: Must state that the sponsored tri-party GC rate basis widens in the last 2-3 business days of quarter-end.
提示: This criterion checks that the response explicitly states the sponsored tri party GC basis widens in final 2-3 pre quarter end days.
出处: prbench:8c4a212c39a9ef81c48b6881 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0702 [必须]
判据: State that sponsor banks' SLR exposure is reduced by 70-90% under FICC clearing compared to triparty.
提示: Balance sheet efficiency mechanism.
出处: prbench:8c4a212c39a9ef81c48b6881 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0703 [必须]
判据: Must describe that FICC sponsored (centrally cleared) repo reduces dealer balance sheet usage via netting/novation/margin offsets (e.g., ~70-90% lower SLR exposure vs plain tri-party).
提示: This criterion captures the core mechanism and magnitude that makes sponsored capacity cheaper at SLR returns. It checks correct understanding of why sponsored is balance sheet lighter.
出处: prbench:8c4a212c39a9ef81c48b6881 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0704 [必须]
判据: The response correctly identifies Singapore’s fund tax exemptions as Section 13O/13U (or 13X).
提示: Prevents conflating domestic fund incentives with treaty relief.
出处: prbench:8df86e7de3c8060e1d3742be | 话题: Taxation & Cross-Border Structuring

## FIN-0705 [必须]
判据: The response clarifies that GIFT tax advantages are instrument-specific rather than a blanket zero on all Indian equity gains.
提示: Prevents over-claiming by tying benefits to “specified securities.”
出处: prbench:8df86e7de3c8060e1d3742be | 话题: Taxation & Cross-Border Structuring

## FIN-0706 [必须]
判据: The response states that for Indian shares acquired on or after April 1, 2017, capital gains are taxed in India.
提示: This is the core post-2017 rule that drives India equity tax outcomes.
出处: prbench:8df86e7de3c8060e1d3742be | 话题: Taxation & Cross-Border Structuring

## FIN-0707 [必须]
判据: The response explains that Mauritius’s 80% partial exemption regime yields about a 3% effective corporate tax, conditional on economic substance.
提示: Mauritius viability hinges on the partial exemption plus real substance.
出处: prbench:8df86e7de3c8060e1d3742be | 话题: Taxation & Cross-Border Structuring

## FIN-0708 [必须]
判据: The response explains that Singapore's fund tax exemptions (i.e., Section 130/13U) are domestic fund exemptions rather than India-treaty benefits.
提示: Important consideration.
出处: prbench:8df86e7de3c8060e1d3742be | 话题: Taxation & Cross-Border Structuring

## FIN-0709 [建议]
判据: The response explicitly states that front-office talent depth is stronger in Singapore than in GIFT or Mauritius.
提示: Hiring depth is a requested dimension and a real execution constraint.
出处: prbench:8df86e7de3c8060e1d3742be | 话题: Taxation & Cross-Border Structuring

## FIN-0710 [建议]
判据: The response fails to explicitly align month-end timestamps across both series before building the spread.
提示: Misaligned dates (or implicit inner joins) can invalidate the test statistics
出处: prbench:8e50a93ec7664db8647d0663 | 话题: Investment Strategy & Portfolio Design

## FIN-0711 [必须]
判据: The response specifies reasonable lag choices (e.g., AIC-selected ADF lags).
提示: Because stationarity tests are sensitive to lags
出处: prbench:8e50a93ec7664db8647d0663 | 话题: Investment Strategy & Portfolio Design

## FIN-0712 [必须]
判据: The response correctly runs KPSS for level stationarity on the spread/residual (does not treat rejection as evidence of stationarity).
提示: Required procedure for doing the test accurately
出处: prbench:8e50a93ec7664db8647d0663 | 话题: Investment Strategy & Portfolio Design

## FIN-0713 [必须]
判据: The response consistently uses either log prices or raw levels across both Engle-Granger and KPSS tests, without mixing them.
提示: Because transformations change beta, spread construction and interpretation.
出处: prbench:8e50a93ec7664db8647d0663 | 话题: Investment Strategy & Portfolio Design

## FIN-0714 [建议]
判据: The response checks continuity of the adjusted price series (e.g., no gaps or jumps after rolling contracts).
提示: Because contaminated inputs can inavalidate tests.
出处: prbench:8e50a93ec7664db8647d0663 | 话题: Investment Strategy & Portfolio Design

## FIN-0715 [必须]
判据: The response builds a standard, continuous, back-adjusted series per symbol before testing (no roll jumps contaminating the spread).
提示: It is absolutely essential and standard practice to back-adjust futures data before performing any sort of analysis with it.
出处: prbench:8e50a93ec7664db8647d0663 | 话题: Investment Strategy & Portfolio Design

## FIN-0716 [必须]
判据: The response provides a conclusion on mean reversion aligned with the calculated stats.
提示: Specifically asked for in the task
出处: prbench:8e50a93ec7664db8647d0663 | 话题: Investment Strategy & Portfolio Design

## FIN-0717 [必须]
判据: The response correctly applies Engle-Granger by estimating the cointegrating relationship and testing the residual/spread (not raw prices) for stationarity/unit roots.
提示: Correctness of the tests require correct procedure
出处: prbench:8e50a93ec7664db8647d0663 | 话题: Investment Strategy & Portfolio Design

## FIN-0718 [建议]
判据: The response recognizes quarterly observation frequency in the structure (by looking at autocall probability and barrier monitoring).
提示: Fixes cadence.
出处: prbench:8e63996c3a1c745e6c2f4de4 | 话题: Derivatives & Structured Products

## FIN-0719 [必须]
判据: The response recognises upside payoff potential under favorable market conditions (e.g., early autocall, low-volatility rally).
提示: Upside outcome.
出处: prbench:8e63996c3a1c745e6c2f4de4 | 话题: Derivatives & Structured Products

## FIN-0720 [负面]
判据: The response misrepresents key product features (e.g., says the barrier is American when it’s European).
提示: Important to accurately define product features.
出处: prbench:8e63996c3a1c745e6c2f4de4 | 话题: Derivatives & Structured Products

## FIN-0721 [必须]
判据: The response correctly identifies that VaR's reliance on historical data makes it backward-looking.
提示: This shows a deeper understanding of VaR's limitations beyond just the issue of tail risk.
出处: prbench:8e79ba69493606c8fc54c270 | 话题: Risk Management & Stress Testing

## FIN-0722 [必须]
判据: The response correctly identifies that VaR has scope gaps (e.g., omitting many Risk-Not-In-VaR (RNIV)).
提示: This shows a deeper understanding of VaR's limitations beyond just the issue of tail risk.
出处: prbench:8e79ba69493606c8fc54c270 | 话题: Risk Management & Stress Testing

## FIN-0723 [必须]
判据: The response correctly identifies that VaR is insensitive to the severity of losses in the tail (i.e., beyond the confidence level).
提示: This is the most fundamental and widely understood theoretical limitation of VaR.
出处: prbench:8e79ba69493606c8fc54c270 | 话题: Risk Management & Stress Testing

## FIN-0724 [必须]
判据: The response correctly identifies that VaR is procyclical (e.g., it understates risk in calm periods and overstates it after a crisis has already occurred).
提示: This shows a deeper understanding of VaR's limitations beyond just the issue of tail risk.
出处: prbench:8e79ba69493606c8fc54c270 | 话题: Risk Management & Stress Testing

## FIN-0725 [必须]
判据: The response identifies that recognizing full contract value upfront based solely on 2+ years' payment history violates ASC 606-10-25-1 collectibility requirements, which require assessing the customer's current ability and intention to pay amounts when due (forward-looking), not past payment behavior.
提示: This is the most egregious violation explicitly stated in the prompt - misunderstanding collectibility requirements is a fundamental criterion that affects whether revenue can be recognized at all, making this the highest restatement risk.
出处: prbench:8eab3309603a1a2b18e2d675 | 话题: Accounting & Financial Statement Analysis

## FIN-0726 [必须]
判据: The response identifies that mid-term contract modifications (upgrades/downgrades/payment term changes) must be analyzed to determine if they are (1) a separate new contract or (2) a modification requiring prospective or retrospective adjustment to the existing contract, per ASC 606-10-25-13.
提示: Addresses the specific concern in the prompt about frequent mid-term modifications and provides the correct accounting framework for analysis.
出处: prbench:8eab3309603a1a2b18e2d675 | 话题: Accounting & Financial Statement Analysis

## FIN-0727 [负面]
判据: The response acknowledges the 75% renewal rate but claims it has no impact on accounting treatment, ignoring the material implications for variable consideration constraint, commission amortization period, and expected contract life.
提示: Ignores explicit information in the prompt that has material implications for multiple aspects of revenue recognition and cost capitalization.
出处: prbench:8eab3309603a1a2b18e2d675 | 话题: Accounting & Financial Statement Analysis

## FIN-0728 [必须]
判据: The response states that implementation services must be a separate Performance Obligation (PO) only if the service is distinct under the two-part test: (1) the customer can benefit from the service on its own or with other readily available resources, AND (2) the service is separately identifiable (not highly interdependent/interrelated) with the SaaS functionality per ASC 606-10-25-19.
提示: This is the core technical principle for determining distinct performance obligations under ASC 606, which drives the entire allocation and timing issue the auditor is raising.
出处: prbench:8eab3309603a1a2b18e2d675 | 话题: Accounting & Financial Statement Analysis

## FIN-0729 [必须]
判据: The response identifies the 35% revenue jump and 20% deferred revenue drop post-ASC 606 adoption as a red flag indicating the company likely incorrectly front-loaded implementation revenue or otherwise accelerated recognition during transition.
提示: Directly connects the specific metrics in the prompt to probable accounting errors and explains why these numbers are concerning indicators of aggressive revenue recognition.
出处: prbench:8eab3309603a1a2b18e2d675 | 话题: Accounting & Financial Statement Analysis

## FIN-0730 [必须]
判据: The response states that if implementation services are a separate PO, the total transaction price must be allocated based on the relative Standalone Selling Price (SSP) of the SaaS and the services per ASC 606-10-32-31.
提示: This is the required allocation method under ASC 606 which dictates the timing and amount of revenue recognition for each performance obligation.
出处: prbench:8eab3309603a1a2b18e2d675 | 话题: Accounting & Financial Statement Analysis

## FIN-0731 [必须]
判据: The response identifies that the 75% renewal rate means variable consideration must be heavily constrained per ASC 606-10-32-11 (constraint on variable consideration), meaning the company should only include amounts in the transaction price for which it is probable that a significant revenue reversal will not occur.
提示: Directly addresses the variable consideration constraint principle which is fundamental to ASC 606 and prevents overstating revenue when there's significant uncertainty about collection or contract completion.
出处: prbench:8eab3309603a1a2b18e2d675 | 话题: Accounting & Financial Statement Analysis

## FIN-0732 [必须]
判据: The response identifies that the sales commission amortization period must equal the expected period of benefit (total expected customer relationship period including expected renewals), not just the initial contract term, per ASC 340-40-35-1.
提示: States the correct general principle for capitalizing customer acquisition costs under ASC 606, which is foundational to evaluating the 3-year amortization.
出处: prbench:8eab3309603a1a2b18e2d675 | 话题: Accounting & Financial Statement Analysis

## FIN-0733 [负面]
判据: The response suggests that the performance guarantee (system uptime SLA) is its own separate Performance Obligation (PO), thus confusing a standard warranty/service-level assurance with a distinct, revenue-generating promise.
提示: This is a major technical mistake that fundamentally mischaracterizes the nature of promises to customers under ASC 606-10-25-18, potentially leading to incorrect PO identification.
出处: prbench:8eab3309603a1a2b18e2d675 | 话题: Accounting & Financial Statement Analysis

## FIN-0734 [必须]
判据: The response correctly identifies that variable consideration based on the number of users must be estimated at contract inception and included in the total transaction price per ASC 606-10-32-5.
提示: Correctly handles a complex aspect of SaaS contracts (usage-based pricing) which must be estimated unless the 'as invoiced' practical expedient applies under ASC 606-10-55-18.
出处: prbench:8eab3309603a1a2b18e2d675 | 话题: Accounting & Financial Statement Analysis

## FIN-0735 [建议]
判据: The response clarifies that the 99.5% SLA uptime guarantee is a service-level assurance or warranty, not a separate performance obligation under ASC 606-10-25-18.
提示: Correctly categorizes the SLA as an assurance-type warranty rather than a distinct promised good or service, preventing incorrect PO identification.
出处: prbench:8eab3309603a1a2b18e2d675 | 话题: Accounting & Financial Statement Analysis

## FIN-0736 [必须]
判据: The response explains why the sum of standalone ES exceeds firm ES (e.g., it attributes the gap to diversification, tied explicitly to the stated dependence assumptions).
提示: Prevents vague answers that ignore portfolio effects.
出处: prbench:8f564df6625763b79cbfd1fc | 话题: Risk Management & Stress Testing

## FIN-0737 [必须]
判据: The response explains that lambda = 0.94 produces approximately a one-month half-life for volatility shocks.
提示: Shows technical understanding of exponential weighting mechanics and directly addresses the user's decay factor question.
出处: prbench:9157fdb635fd8664f2b7fcc4 | 话题: Risk Management & Stress Testing

## FIN-0738 [必须]
判据: The response interprets beta = 0.91 as indicating high volatility persistence (e.g., by suggesting that it produces a seven-day half-life and causes the whipsaw effect).
提示: Validates the user's own calculation and explains the mechanism behind reactive VaR behavior.
出处: prbench:9157fdb635fd8664f2b7fcc4 | 话题: Risk Management & Stress Testing

## FIN-0739 [负面]
判据: The response treats historical simulation VaR and parametric VaR as interchangeable.
提示: VaR methodologies have fundamentally different assumptions; conflating them shows lack of technical depth.
出处: prbench:9157fdb635fd8664f2b7fcc4 | 话题: Risk Management & Stress Testing

## FIN-0740 [必须]
判据: The response notes that filtered historical simulation (FHS) preserves non-normal tail characteristics from empirical return distributions.
提示: Explains why FHS-GARCH is superior to parametric alternatives for the rates book with non-linear exposures.
出处: prbench:9157fdb635fd8664f2b7fcc4 | 话题: Risk Management & Stress Testing

## FIN-0741 [必须]
判据: The response diagnoses the breach clustering as evidence of a volatility regime shift rather than pure fat-tailed distribution issues.
提示: Correctly identifying the root cause (regime change vs. fat tails) determines the appropriate model fix and regulatory justification.
出处: prbench:9157fdb635fd8664f2b7fcc4 | 话题: Risk Management & Stress Testing

## FIN-0742 [建议]
判据: The response explains that reactive VaR (i.e., responding quickly to market moves) is actually more accurate than artificially smoothed measures.
提示: Reframes the 'problem' as a feature, helping the user defend model behavior to the desk and committee.
出处: prbench:9157fdb635fd8664f2b7fcc4 | 话题: Risk Management & Stress Testing

## FIN-0743 [必须]
判据: The response identifies that short gamma positions on swaptions create convexity risk that linear historical simulation VaR inherently understates.
提示: Explains why the rates book specifically generated breaches—non-linear payoffs require different treatment.
出处: prbench:9157fdb635fd8664f2b7fcc4 | 话题: Risk Management & Stress Testing

## FIN-0744 [必须]
判据: The response explains that filtered historical simulation (FHS) adjusts historical returns for time-varying volatility using GARCH scaling.
提示: Clarifies the mechanism by which FHS addresses the regime-change problem identified in the prompt.
出处: prbench:9157fdb635fd8664f2b7fcc4 | 话题: Risk Management & Stress Testing

## FIN-0745 [必须]
判据: The response analyzes the impact of integration costs on pro forma debt capacity (e.g., reducing available EBITDA for debt service calculations).
提示: Integration costs reduce available cash flows and affect debt capacity calculations.
出处: prbench:916292ce89cc3d1d8661ab4a | 话题: Corporate Finance

## FIN-0746 [必须]
判据: The response analyzes the impact of EBITDA volatility on debt service capacity (e.g., calculating how the $90mm EBITDA decline affects interest coverage ratios or available cash for debt payments).
提示: Understanding how EBITDA volatility affects the target's ability to service debt is crucial for deal structuring and risk assessment.
出处: prbench:916292ce89cc3d1d8661ab4a | 话题: Corporate Finance

## FIN-0747 [必须]
判据: The response addresses make-whole provision costs associated with early repayment of the mezzanine debt (e.g., calculating prepayment penalties and yield maintenance fees, or estimating costs as a percentage of outstanding principal).
提示: Make-whole provisions represent a significant cost that must be quantified to determine refinancing feasibility.
出处: prbench:916292ce89cc3d1d8661ab4a | 话题: Corporate Finance

## FIN-0748 [负面]
判据: The response calculates enterprise value using outdated EBITDA figures (e.g., $380mm instead of the current $290mm).
提示: Using incorrect EBITDA figures fundamentally undermines the valuation analysis and leads to erroneous conclusions.
出处: prbench:916292ce89cc3d1d8661ab4a | 话题: Corporate Finance

## FIN-0749 [必须]
判据: The response analyzes the impact of EBITDA volatility on covenant compliance (e.g., showing how debt-to-EBITDA ratios change from 4.2x to potentially 5.5x based on the EBITDA decline, affecting covenant headroom).
提示: Understanding how EBITDA volatility affects the target's ability to service debt is crucial for deal structuring and risk assessment.
出处: prbench:916292ce89cc3d1d8661ab4a | 话题: Corporate Finance

## FIN-0750 [必须]
判据: The response factors make-whole provision costs into the net present value analysis by adjusting initial cash outflows (e.g., "refinancing saves $22mm annually but requires $50mm make-whole payment, yielding positive NPV after 2.3 years").
提示: NPV analysis incorporating all costs is essential for making an economically sound refinancing decision.
出处: prbench:916292ce89cc3d1d8661ab4a | 话题: Corporate Finance

## FIN-0751 [必须]
判据: The response calculates covenant headroom under the proposed new capital structure (e.g., determining debt-to-EBITDA ratios, interest coverage ratios, or minimum liquidity requirements post-acquisition).
提示: Covenant headroom analysis is essential for ensuring the target can operate within debt agreement constraints post-transaction.
出处: prbench:916292ce89cc3d1d8661ab4a | 话题: Corporate Finance

## FIN-0752 [必须]
判据: The response evaluates the target's debt capacity at the acquirer's 2.5-3x leverage target (e.g., approximately $725mm-$870mm based on current EBITDA).
提示: Debt capacity analysis is crucial for determining feasible post-acquisition capital structure and financing requirements.
出处: prbench:916292ce89cc3d1d8661ab4a | 话题: Corporate Finance

## FIN-0753 [负面]
判据: The response treats the 12% mezzanine debt rate as market-appropriate without recognizing it as significantly above-market compared to the acquirer's 6.5% WACC.
提示: Overlooking the substantial cost savings opportunity demonstrates poor financial analysis.
出处: prbench:916292ce89cc3d1d8661ab4a | 话题: Corporate Finance

## FIN-0754 [必须]
判据: The response calculates the implied enterprise value as $2.465 billion (e.g., 8.5x EBITDA multiple x $290mm current-year EBITDA).
提示: This core valuation calculation is fundamental to evaluating the acquisition and serves as the basis for all subsequent financing analysis.
出处: prbench:916292ce89cc3d1d8661ab4a | 话题: Corporate Finance

## FIN-0755 [必须]
判据: The response calculates annual interest savings from replacing the $400mm Mezz debt by comparing the 12% rate to an explicitly stated market-rate debt coupon (e.g., 7-9%).
提示: Interest savings calculation is critical for determining the financial benefit of refinancing and informing the optimal capital structure decision.
出处: prbench:916292ce89cc3d1d8661ab4a | 话题: Corporate Finance

## FIN-0756 [必须]
判据: The response utilizes the correct reinvestment rate formula preferred by investment analysts evaluating large CapEx expenditures: reinvestment rate = CapEx/OCF.
提示: The correct formula allows for an accurate understanding of how much is truly being reinvested.
出处: prbench:91e69ac168d1693c26ae48b2 | 话题: Corporate Finance

## FIN-0757 [必须]
判据: The response recognizes that the investment is not self-funding based on the financial metrics provided.
提示: This is an important callout for a high-quality response, but not strictly required as there are some alternative answers.
出处: prbench:91e69ac168d1693c26ae48b2 | 话题: Corporate Finance

## FIN-0758 [必须]
判据: The response correctly calculates the reinvestment rate as $18 million in CapEx / $11.2 million in OCF = 160.7%.
提示: The correct calculation is important for understanding how much additional capital is required to fund the investment and its relative burden on the company.
出处: prbench:91e69ac168d1693c26ae48b2 | 话题: Corporate Finance

## FIN-0759 [必须]
判据: The response recognizes that valuation metrics (e.g., P/E, EV/EBITDA) can become compressed when CapEx is elevated relative to FCF.
提示: This is an important callout for a high quality response, but not strictly required as there are alternative answers.
出处: prbench:91e69ac168d1693c26ae48b2 | 话题: Corporate Finance

## FIN-0760 [建议]
判据: The response acknowledges that AI infrastructure is a more capital-intensive business than other AI businesses (e.g., AI chatbots, AI services, AI industry solutions).
提示: This is useful contextual awareness, but not strictly required for a good response.
出处: prbench:91e69ac168d1693c26ae48b2 | 话题: Corporate Finance

## FIN-0761 [负面]
判据: The response makes factually incorrect statements about the company's financials or AI market dynamics (e.g., misstating the CapEx amount, operating margins, or revenue figures provided).
提示: Essential to keep accurate.
出处: prbench:91e69ac168d1693c26ae48b2 | 话题: Corporate Finance

## FIN-0762 [必须]
判据: The response defines Debt Service Coverage Ratio (DSCR) as Operating Cash Flow ÷ Total Debt Service.
提示: Provides the primary affordability ratio.
出处: prbench:91ea5c486e239d6f36c8e417 | 话题: Corporate Finance

## FIN-0763 [必须]
判据: The response states that if the after-tax cost of debt is lower than the assumed cost of equity, using more debt (within covenant limits) reduces the firm’s weighted average cost of capital (WACC).
提示: Isolates the financing choice’s direct impact on WACC.
出处: prbench:91ea5c486e239d6f36c8e417 | 话题: Corporate Finance

## FIN-0764 [必须]
判据: The response defines the Interest Coverage Ratio (ICR) as EBIT ÷ Interest Expense.
提示: This oversimplification may mislead users who don’t know the difference between cash flow and EBIT.
出处: prbench:91ea5c486e239d6f36c8e417 | 话题: Corporate Finance

## FIN-0765 [必须]
判据: The response states the after-tax cost of debt formula r_d (1-T).
提示: Objectively compares debt cost on a post-tax basis.
出处: prbench:91ea5c486e239d6f36c8e417 | 话题: Corporate Finance

## FIN-0766 [必须]
判据: The response states that debt financing does not dilute ownership, unlike equity.
提示: Captures a core ownership implication in one line.
出处: prbench:91ea5c486e239d6f36c8e417 | 话题: Corporate Finance

## FIN-0767 [负面]
判据: The response claims investors can deduct 100% of solar costs immediately in the first year.
提示: Factually incorrect tax guidance that could lead to compliance issues.
出处: prbench:9367a4ad8d0666e7e365438b | 话题: Alternative Investments & Private Markets

## FIN-0768 [必须]
判据: The response identifies solar investments as having 15-25-year investment horizons.
提示: Time horizon is fundamental to alternative investment evaluation.
出处: prbench:9367a4ad8d0666e7e365438b | 话题: Alternative Investments & Private Markets

## FIN-0769 [必须]
判据: The response provides Internal Rate of Return (IRR) expectations between 6% and 15% for solar investments.
提示: Realistic return expectations are crucial for proper investment evaluation.
出处: prbench:9367a4ad8d0666e7e365438b | 话题: Alternative Investments & Private Markets

## FIN-0770 [必须]
判据: The response explains that the user's referenced $5.25 million deduction represents MACRS depreciation in year one of a $30 million solar project.
提示: Component analysis enables better investment evaluation.
出处: prbench:9367a4ad8d0666e7e365438b | 话题: Alternative Investments & Private Markets

## FIN-0771 [必须]
判据: The response identifies the federal Investment Tax Credit (ITC) as providing a 30% tax credit on solar installation costs.
提示: Primary tax benefit that drives solar investment returns - must be accurately identified.
出处: prbench:9367a4ad8d0666e7e365438b | 话题: Alternative Investments & Private Markets

## FIN-0772 [必须]
判据: The response mentions that solar panel output typically degrades 0.5-0.8% annually, affecting long-term returns.
提示: Material risk factor affecting long-term investment performance.
出处: prbench:9367a4ad8d0666e7e365438b | 话题: Alternative Investments & Private Markets

## FIN-0773 [必须]
判据: The response states that the unused Investment Tax Credit can be carried forward for up to 5 years if not fully utilized in the first year.
提示: Directly answers the user's concern about losing unused tax benefits.
出处: prbench:9367a4ad8d0666e7e365438b | 话题: Alternative Investments & Private Markets

## FIN-0774 [必须]
判据: The response mentions that the solar ITC tax basis must be reduced by 50% when using both ITC and MACRS depreciation.
提示: Professional guidance essential for complex tax planning decisions.
出处: prbench:9367a4ad8d0666e7e365438b | 话题: Alternative Investments & Private Markets

## FIN-0775 [必须]
判据: The response mentions the Modified Accelerated Cost Recovery System (MACRS), which allows for 5-year accelerated depreciation for solar equipment.
提示: Second major tax benefit component affecting investment returns.
出处: prbench:9367a4ad8d0666e7e365438b | 话题: Alternative Investments & Private Markets

## FIN-0776 [负面]
判据: The response claims that solar investments qualify for 100% bonus depreciation in the same year as claiming the Investment Tax Credit.
提示: Misleading investment guidance that overstates certainty of returns.
出处: prbench:9367a4ad8d0666e7e365438b | 话题: Alternative Investments & Private Markets

## FIN-0777 [必须]
判据: The response states that the deemed cost of the associate on September 1st, 2024 is the additional 20% of $4,800,000 acquired on that date.
提示: Deemed cost
出处: prbench:95466d89963cf1c3e2ae5e74 | 话题: Accounting & Financial Statement Analysis

## FIN-0778 [必须]
判据: The response states that the ending balance of the investment is $6,952,500.
提示: Final answer.
出处: prbench:95466d89963cf1c3e2ae5e74 | 话题: Accounting & Financial Statement Analysis

## FIN-0779 [必须]
判据: The response explicitly states that only the unrealized portion of accumulated OCI should be reclassified to the equity method.
提示: Important IFRS detail.
出处: prbench:95466d89963cf1c3e2ae5e74 | 话题: Accounting & Financial Statement Analysis

## FIN-0780 [必须]
判据: The response explicitly recognizes that fair value gains or losses prior to the equity reclassification could change the deferred tax base after the transition (e.g., FVOCI fair value below cost at transition equates to a lower carrying amount than the tax base; investments adjusted upwards before the transition would include a fair value uplift).
提示: Important concept for the reclassification to equity method.
出处: prbench:95466d89963cf1c3e2ae5e74 | 话题: Accounting & Financial Statement Analysis

## FIN-0781 [负面]
判据: The response shows that the calculation begins with the original $2,000,000 purchase.
提示: The response must explicitly show that the calculation begins with the deemed cost of $7,200,000 on September 1, 2024, and not with the original $2,000,000 purchase
出处: prbench:95466d89963cf1c3e2ae5e74 | 话题: Accounting & Financial Statement Analysis

## FIN-0782 [必须]
判据: The response recognizes that FVOCI equity instruments should be treated as non-recyclable (i.e., impacting retained earnings, not P&L).
提示: IFRS 9 rule.
出处: prbench:95466d89963cf1c3e2ae5e74 | 话题: Accounting & Financial Statement Analysis

## FIN-0783 [必须]
判据: The response identifies September 1st, 2024 as the switch date when significant influence begins.
提示: Determines when to shift from fair value accounting to the equity method (Sept 1, 2024).
出处: prbench:95466d89963cf1c3e2ae5e74 | 话题: Accounting & Financial Statement Analysis

## FIN-0784 [必须]
判据: The response calculates the investor’s share of the investee’s other comprehensive income (OCI) for September to December 2024 as the 2024 annual OCI of $400,000 apportioned over 4/12 of the year, resulting in $133,333.
提示: Share of investee’s
出处: prbench:95466d89963cf1c3e2ae5e74 | 话题: Accounting & Financial Statement Analysis

## FIN-0785 [必须]
判据: The response explicitly states that deferred tax for the equity method transition should use the substantive tax rate for capital gains realization (i.e., as opposed to the standard corporate income tax).
提示: Important IFRS detail.
出处: prbench:95466d89963cf1c3e2ae5e74 | 话题: Accounting & Financial Statement Analysis

## FIN-0786 [建议]
判据: The response states that the investor’s 30% share of the basis difference adjustment is $41,667 × 30% = $12,500.
提示: Investor’s 30% share
出处: prbench:95466d89963cf1c3e2ae5e74 | 话题: Accounting & Financial Statement Analysis

## FIN-0787 [建议]
判据: The response states that the deemed cost of the associate on September 1st, 2024, includes remeasuring the previously held 10% stake at its fair value of $2,400,000.
提示: Continuous cost
出处: prbench:95466d89963cf1c3e2ae5e74 | 话题: Accounting & Financial Statement Analysis

## FIN-0788 [必须]
判据: The response mentions that because the fair value is lower than the book value (i.e., the investee is depreciating relative to the fair value basis), a share of this excess depreciation must be added back to equity income.
提示: add back our share to equity income.
出处: prbench:95466d89963cf1c3e2ae5e74 | 话题: Accounting & Financial Statement Analysis

## FIN-0789 [必须]
判据: The response recognizes that reclassification to the equity method could trigger deferred tax adjustments (e.g., Unrealized FVOCI gains or loss carryforwards).
提示: Related to the reclassification question.
出处: prbench:95466d89963cf1c3e2ae5e74 | 话题: Accounting & Financial Statement Analysis

## FIN-0790 [必须]
判据: The response explains that it takes time for a project to realize its full revenue stream in Hollywood Accounting.
提示: The user is specifically asking why the movie isn't profitable despite it's initial release.
出处: prbench:9796c708c04b1362fe64948c | 话题: Accounting & Financial Statement Analysis

## FIN-0791 [建议]
判据: The response interprets a "participation statement" in Hollywood Accounting (e.g., why it might show zero until breakeven under the contract's defined metrics).
提示: Understanding the signed participation statement helps the user to understand the non-payment situation better.
出处: prbench:9796c708c04b1362fe64948c | 话题: Accounting & Financial Statement Analysis

## FIN-0792 [必须]
判据: The response states that in Hollywood Accounting, the movie theater keeps a large percentage (e.g., 50%+) of total box office revenue.
提示: Vital piece of information in tying box office performance to actual studio revenue.
出处: prbench:9796c708c04b1362fe64948c | 话题: Accounting & Financial Statement Analysis

## FIN-0793 [必须]
判据: The response distinguishes Hollywood Accounting compensation streams (e.g., upfront salary, contingent compensation/back-end, box-office bonuses, union residuals).
提示: It is very important to understand compensation streams for Hollywood Accounting.
出处: prbench:9796c708c04b1362fe64948c | 话题: Accounting & Financial Statement Analysis

## FIN-0794 [建议]
判据: The response explains the profit recoupment waterfall that keeps net profit negative (e.g., distributor fees, P&A marketing recoupment, overhead, interest, senior participation and residuals, cross-collateralization).
提示: This connects to why a participation statement can show zero.
出处: prbench:9796c708c04b1362fe64948c | 话题: Accounting & Financial Statement Analysis

## FIN-0795 [必须]
判据: The response explains why box-office success doesn’t equal immediate payment (e.g., a film's good initial run at the box office is the first of many revenue streams).
提示: This explains the reason why a #1 first run won't bring immediate payment.
出处: prbench:9796c708c04b1362fe64948c | 话题: Accounting & Financial Statement Analysis

## FIN-0796 [必须]
判据: The response converts all key volume metrics (daily ATOM, 30-day avg, 24H USD volume) into USD terms.
提示: This is essential to assess liquidity and trading capacity in 'normal' monetary terms.
出处: prbench:97bd8567adde015b5464e552 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0797 [必须]
判据: The response calculates the minimum EBITDA required to maintain 1.25x debt service coverage for MidCorp's debt structure (e.g., an annual debt service of $25M requiring a minimum of $31.25M EBITDA).
提示: Covenant compliance analysis ensures MidCorp's financing structure viability.
出处: prbench:983053d28ab617a3b32eea06 | 话题: Alternative Investments & Private Markets

## FIN-0798 [必须]
判据: The response validates that MidCorp's debt-to-total capital ratio remains below the 65% threshold (e.g., $315M debt vs $500M total capital = 63%).
提示: Fund investment criteria compliance ensures MidCorp deal meets mandate requirements.
出处: prbench:983053d28ab617a3b32eea06 | 话题: Alternative Investments & Private Markets

## FIN-0799 [必须]
判据: The response calculates MidCorp's enterprise value by: $42M EBITDA * a multiple between 11.5x and 12.8x = a purchase price between $483M and $538M.
提示: Accurate valuation of this specific target is fundamental to the LBO analysis.
出处: prbench:983053d28ab617a3b32eea06 | 话题: Alternative Investments & Private Markets

## FIN-0800 [必须]
判据: The response projects MidCorp's revenue growth from a $280M baseline using the specified 8-12% annual growth rates.
提示: Revenue projections must reflect MidCorp's specific growth characteristics.
出处: prbench:983053d28ab617a3b32eea06 | 话题: Alternative Investments & Private Markets

## FIN-0801 [必须]
判据: The response models MidCorp's EBITDA margin progression (e.g., from the current 15% baseline to the target 19-21% over 4 years) incorporating the $18M automation capex investment.
提示: MidCorp's specific operational improvement thesis must be explicitly modeled.
出处: prbench:983053d28ab617a3b32eea06 | 话题: Alternative Investments & Private Markets

## FIN-0802 [必须]
判据: The response calculates total debt as $315M by applying leverage multiples to $42M EBITDA: 5.5x first lien ($231M) + 1.2x second lien ($50.4M) + 0.8x mezzanine ($33.6M).
提示: Proper debt sizing for MidCorp's specific leverage structure determines equity requirements.
出处: prbench:983053d28ab617a3b32eea06 | 话题: Alternative Investments & Private Markets

## FIN-0803 [必须]
判据: The response calculates management's equity multiple as (15% ownership × total equity value at exit) ÷ (15% × current enterprise value).
提示: Management retention depends on achieving their specific 5x equity multiple threshold.
出处: prbench:983053d28ab617a3b32eea06 | 话题: Alternative Investments & Private Markets

## FIN-0804 [必须]
判据: The response models working capital reduction from 12% to 8% of revenue by year 2, calculating specific cash release amounts (e.g., a 4% improvement on projected revenue levels).
提示: Working capital optimization significantly impacts MidCorp's cash generation.
出处: prbench:983053d28ab617a3b32eea06 | 话题: Alternative Investments & Private Markets

## FIN-0805 [必须]
判据: The response explains management's equity multiple as: if exit equity value is $400M, then ($60M exit value) ÷ ($12M initial rollover based on current valuation) = 5x multiple.
提示: This is an important example.
出处: prbench:983053d28ab617a3b32eea06 | 话题: Alternative Investments & Private Markets

## FIN-0806 [负面]
判据: The response contains calculation errors in MidCorp-specific LBO metrics (e.g., incorrect enterprise value from EBITDA multiples, debt capacity miscalculations from leverage ratios, or IRR errors affecting investment decisions).
提示: Mathematical errors in MidCorp analysis undermine investment committee confidence and decision accuracy.
出处: prbench:983053d28ab617a3b32eea06 | 话题: Alternative Investments & Private Markets

## FIN-0807 [必须]
判据: NO CHANGE.
提示: Monthly liquidity management is critical during MidCorp's operational transformation when large capex investments ($9M in Year 1, $9M in Year 2) and working capital optimization (12% to 8% reduction) create significant cash flow timing risks that could trigger covenant violations or require additional revolver draws.
出处: prbench:983053d28ab617a3b32eea06 | 话题: Alternative Investments & Private Markets

## FIN-0808 [必须]
判据: The response considers the long-term compounding effects (e.g., how sustained equity exposure can boost retirement balances over decades).
提示: The response considers the long-term compounding effect (e.g., how sustained equity exposure can boost retirement balances over decades).
出处: prbench:989bcc576366697f0e2408c4 | 话题: Wealth Management, Financial Planning & Advice

## FIN-0809 [负面]
判据: Reports CVaR, tracking error, or drawdown without consistent horizon/confidence or method, or uses definitions that conflict with those used elsewhere in the write-up.
提示: Inconsistent or undefined metrics invalidate risk comparisons.
出处: prbench:992c616d92c1f3a48611eb8a | 话题: Investment Strategy & Portfolio Design

## FIN-0810 [必须]
判据: Defines a benchmark (e.g., 60/40) and computes tracking error versus the proposed portfolio using the same covariance matrix.
提示: TE requires a clear reference and consistent inputs.
出处: prbench:992c616d92c1f3a48611eb8a | 话题: Investment Strategy & Portfolio Design

## FIN-0811 [必须]
判据: The response correctly justifies the use of options by explaining they provide the right, but not the obligation, to transact.
提示: Using options to manage contingent risk is a foundational concept in corporate treasury.
出处: prbench:993ce66b0c827f49847c06e5 | 话题: International Finance & FX Hedging

## FIN-0812 [建议]
判据: Where a sale is discussed, the response explains how any surplus or deficit is treated.
提示: Complete understanding of the mechanics of a forced sale.
出处: prbench:9ded6978c5236e3e6444a1cf | 话题: Alternative Investments & Private Markets

## FIN-0813 [建议]
判据: Where a sale is discussed, the response explains that proceeds are first used to cover the defaulted amount, interest, and costs.
提示: The order of application for recovered funds.
出处: prbench:9ded6978c5236e3e6444a1cf | 话题: Alternative Investments & Private Markets

## FIN-0814 [必须]
判据: The response identifies TSMC’s position in producing advanced semiconductor nodes (e.g., 5nm or 3nm).
提示: These nodes are central to TSMC’s technological lead and directly influence margins and client acquisition.
出处: prbench:a0fb14b4845312653c684c57 | 话题: Accounting & Financial Statement Analysis

## FIN-0815 [负面]
判据: The response incorrectly characterizes a UK retail CBDC as a direct, non-intermediated model where users hold accounts directly with the Bank of England.
提示: This is a significant factual error that demonstrates a fundamental misunderstanding of the UK's proposed CBDC design, which is explicitly "intermediated"[cite: 340]. It would undermine the credibility of the entire response.
出处: prbench:a1a8f98ec83491a6b28248c1 | 话题: FinTech, Crypto & Digital Assets

## FIN-0816 [必须]
判据: The response correctly identifies that a digital pound is a direct, risk-free claim on the Bank of England.
提示: A foundational point of understanding necessary for the analysis.
出处: prbench:a1a8f98ec83491a6b28248c1 | 话题: FinTech, Crypto & Digital Assets

## FIN-0817 [必须]
判据: Response identifies that the rouble appears to be weakening.
提示: Good analysis for the model to recognise, as a weakening rouble makes the option more attractive. This potential weakening is based on the previous spot rates and forward contract discount.
出处: prbench:a2dbc89c63c18401e9aa1266 | 话题: International Finance & FX Hedging

## FIN-0818 [必须]
判据: Response states that the net sterling payment of the forward contract is approximately £1,846 cheaper than the net sterling payment from the exercised options.
提示: A key piece of analysis to include.
出处: prbench:a2dbc89c63c18401e9aa1266 | 话题: International Finance & FX Hedging

## FIN-0819 [必须]
判据: Response correctly identifies that a call option should be used instead of a put option.
提示: This must be accurate for the final net sterling receipt figure to be accurate.
出处: prbench:a2dbc89c63c18401e9aa1266 | 话题: International Finance & FX Hedging

## FIN-0820 [必须]
判据: Response correctly calculates the net sterling payment from the options as approximately £1,836,523 assuming it is exercised.
提示: The correct final figure for the call option.
出处: prbench:a2dbc89c63c18401e9aa1266 | 话题: International Finance & FX Hedging

## FIN-0821 [必须]
判据: Response adds the discount to the spot rate to calculate the correct forward rate, which is 79.36.
提示: This must be accurate for the final net sterling receipt figure to be accurate.
出处: prbench:a2dbc89c63c18401e9aa1266 | 话题: International Finance & FX Hedging

## FIN-0822 [必须]
判据: Response selects the correct discount rate for calculating the forward rate, 0.55.
提示: This must be accurate for the final net sterling receipt figure to be accurate.
出处: prbench:a2dbc89c63c18401e9aa1266 | 话题: International Finance & FX Hedging

## FIN-0823 [必须]
判据: Response selects the correct spot rate of 78.81 when calculating the correct forward rate.
提示: This must be accurate for the final net sterling receipt figure to be accurate.
出处: prbench:a2dbc89c63c18401e9aa1266 | 话题: International Finance & FX Hedging

## FIN-0824 [必须]
判据: Response correctly calculates the option premium to be £13,104.
提示: This must be accurate for the final net sterling receipt figure to be accurate.
出处: prbench:a2dbc89c63c18401e9aa1266 | 话题: International Finance & FX Hedging

## FIN-0825 [必须]
判据: Response divides the rouble payment of 145.6 million by the correctly calculated forward rate of 79.36, to get the correct net sterling payment from the forward contract of approximately £1,834,677.
提示: This is the correct figure for the forward contract.
出处: prbench:a2dbc89c63c18401e9aa1266 | 话题: International Finance & FX Hedging

## FIN-0826 [必须]
判据: The response presents expected net LP return = fee APR − expected IL/LVR − operating costs (gas, rebalancing), with at least one numeric example.
提示: Synthesis into a net return framework is essential. Prevents metric-by-metric answers without economic interpretation.
出处: prbench:a4a6bce111982d13689c20a6 | 话题: FinTech, Crypto & Digital Assets

## FIN-0827 [必须]
判据: The response explains how choosing narrower vs wider ranges in Uniswap v3 affects impermanent loss and fee capture, with at least one numeric illustration of time-in-range outcomes.
提示: Range width is fundamental to balancing impermanent loss against fee generation. Including a numeric example ensures clarity and prevents vague answers.
出处: prbench:a4a6bce111982d13689c20a6 | 话题: FinTech, Crypto & Digital Assets

## FIN-0828 [必须]
判据: The response explains that the connected party override rules generally deny corporation tax relief for creditor impairment debits (e.g., due to assumed group-level neutrality and anti-avoidance safeguard rules).
提示: The fundamental principle that governs the tax treatment of the impairment.
出处: prbench:a4cde836ec97551626e4a3f9 | 话题: Taxation & Cross-Border Structuring

## FIN-0829 [必须]
判据: The response states that a sale of the debt while the companies are connected will not generate a tax-deductible loss for the UK creditor company.
提示: The tax treatment of a related transaction is a fundamental part of UK tax law.
出处: prbench:a4cde836ec97551626e4a3f9 | 话题: Taxation & Cross-Border Structuring

## FIN-0830 [必须]
判据: The response identifies the sale of the loan as a related transaction under the loan relationships regime.
提示: The technical rule that determines the tax treatment of the sale.
出处: prbench:a4cde836ec97551626e4a3f9 | 话题: Taxation & Cross-Border Structuring

## FIN-0831 [必须]
判据: The response states that waiving the debt while the companies are connected will not generate a tax-deductible loss for the UK creditor company under the loan relationships connected party rules.
提示: Core UK tax law principle that connected party debt releases don't generate allowable losses. Fundamental to understanding the loan relationships regime.
出处: prbench:a4cde836ec97551626e4a3f9 | 话题: Taxation & Cross-Border Structuring

## FIN-0832 [建议]
判据: The response explains that the corporate rescue exemption under South African tax law is a debtor-focused relief that does not create corresponding creditor deductions.
提示: Clarifies misconceptions about tax symmetry in debt restructuring.
出处: prbench:a4cde836ec97551626e4a3f9 | 话题: Taxation & Cross-Border Structuring

## FIN-0833 [必须]
判据: The response identifies the 50% control test under CTA 2009 that determines connected party status for the loan relationships regime.
提示: Fundamental threshold for applying connected party rules.
出处: prbench:a4cde836ec97551626e4a3f9 | 话题: Taxation & Cross-Border Structuring

## FIN-0834 [必须]
判据: The response explains that connected party override rules in CTA 2009 generally deny corporation tax relief for impairment debits and release debits when companies remain connected.
提示: The central mechanism of UK-connected companies' anti-avoidance rules. Essential for both strategic options analysis.
出处: prbench:a4cde836ec97551626e4a3f9 | 话题: Taxation & Cross-Border Structuring

## FIN-0835 [必须]
判据: The response explains that the connected party override rules also deny corporation tax relief for creditor release debits.
提示: The denial of release debits is a key tenet of the connected-party rules.
出处: prbench:a4cde836ec97551626e4a3f9 | 话题: Taxation & Cross-Border Structuring

## FIN-0836 [建议]
判据: The response explains the misalignment between the IFRS 9 accounting treatment and the tax treatment (e.g., IFRS 9 requires ECL recognition, but tax relief is denied; P&L would show an impairment debit, but no deductible loan-relationship debit is in play for corporate taxes).
提示: Explaining the book tax difference.
出处: prbench:a4cde836ec97551626e4a3f9 | 话题: Taxation & Cross-Border Structuring

## FIN-0837 [建议]
判据: The response explains that tax relief is only available for impairment losses that accrue post-disposal.
提示: This is a specific technical point of the connected party rules.
出处: prbench:a4cde836ec97551626e4a3f9 | 话题: Taxation & Cross-Border Structuring

## FIN-0838 [必须]
判据: The response attributes wide spreads to dealer balance-sheet/inventory constraints or regulatory capital costs for warehousing risk.
提示: Links microstructure to dealer intermediation capacity and capital constraints.
出处: prbench:a69235c6c14cf8964deee783 | 话题: Market Microstructure, Trading & Liquidity

## FIN-0839 [必须]
判据: The response evaluates whether TSMC's calculated Tobin's Q (4.0-5.5 range) represents market overvaluation (over 2).
提示: Professional analysis questions whether extremely high Q reflects bubble risk.
出处: prbench:a7547bde6081d65475eb57d5 | 话题: Accounting & Financial Statement Analysis

## FIN-0840 [必须]
判据: The response calculates implied cost of equity justifying market P/B 6.3x by algebraically solving 6.3 = 1 + [(17% - r) ÷ (r - 5%)] for r, yielding r ≈ 6.90%.
提示: Reverse-engineering implied cost of equity tests market pricing assumption realism.
出处: prbench:a7547bde6081d65475eb57d5 | 话题: Accounting & Financial Statement Analysis

## FIN-0841 [必须]
判据: The response converts Taiwan's ordinary share price of NT$950 to USD using an exchange rate of 31.5:1, yielding $30.16 per ordinary share.
提示: Foundational currency conversion enables cross-market price comparison.
出处: prbench:a7547bde6081d65475eb57d5 | 话题: Accounting & Financial Statement Analysis

## FIN-0842 [必须]
判据: The response calculates the residual income model intrinsic value per share as $50.04 using the perpetual growth RIM formula: Value per Share = [Book Equity + (Residual Income ÷ (r - g))] ÷ Shares Outstanding, where Residual Income = (ROE - r) × Book Equity, with inputs ROE 17%, r 12%, g 5%, book equity $151.8B, shares 5.2B.
提示: Full per-share RIM valuation enables direct comparison to market price.
出处: prbench:a7547bde6081d65475eb57d5 | 话题: Accounting & Financial Statement Analysis

## FIN-0843 [必须]
判据: The response calculates the break-even ROE required to justify market P/B of 6.3x under RIM by solving 6.3 = 1 + [(ROE - 12%) ÷ (12% - 5%)] for ROE, yielding ROE ≈49.1% (allowing a rounding tolerance of ±0.2 percentage points).
提示: Testing break-even ROE reveals the implausibility of current valuation.
出处: prbench:a7547bde6081d65475eb57d5 | 话题: Accounting & Financial Statement Analysis

## FIN-0844 [必须]
判据: The response calculates RIM-justified price-to-book ratio: 1 + [(17% ROE - 12% r) ÷ (12% r - 5% g)] = 1 + (5% ÷ 7%) = 1.714x.
提示: Theoretical benchmark for contradiction assessment against actual 6.3x.
出处: prbench:a7547bde6081d65475eb57d5 | 话题: Accounting & Financial Statement Analysis

## FIN-0845 [必须]
判据: The response compares the arbitrage spread in bps (22.6% = 2,260 bps) to the FX cost threshold (15-25 bps).
提示: After accounting for FX costs.
出处: prbench:a7547bde6081d65475eb57d5 | 话题: Accounting & Financial Statement Analysis

## FIN-0846 [建议]
判据: The response explains that Q > 1 signals firms should invest more (the market values assets above replacement cost, indicating positive NPV projects).
提示: Prompt asks what Q>2 signals about capital allocation efficiency extended.
出处: prbench:a7547bde6081d65475eb57d5 | 话题: Accounting & Financial Statement Analysis

## FIN-0847 [必须]
判据: The response calculates the arbitrage spread as 22.6% using the formula: ($37.00 - $30.16) ÷ $30.16 = 22.6%.
提示: Quantifies gross arbitrage opportunity before transaction cost analysis.
出处: prbench:a7547bde6081d65475eb57d5 | 话题: Accounting & Financial Statement Analysis

## FIN-0848 [建议]
判据: The response calculates market capitalisation as $962 billion: $185 × 5.2B shares outstanding = $962B.
提示: Establishes equity valuation baseline.
出处: prbench:a7547bde6081d65475eb57d5 | 话题: Accounting & Financial Statement Analysis

## FIN-0849 [必须]
判据: The response explains Q > 2 signals abundant high-return reinvestment opportunities where marginal capital returns significantly exceed hurdle rates.
提示: Prompt asks what Q>2 signals about capital allocation efficiency.
出处: prbench:a7547bde6081d65475eb57d5 | 话题: Accounting & Financial Statement Analysis

## FIN-0850 [必须]
判据: The response quantifies the magnitude by which the market price ($185) exceeds the residual income model value as either a 270% overvaluation (calculated as ($185 - $50.04) ÷ $50.04 = 270%) or 3.7 times the RIM value ($185 ÷ $50.04 = 3.7×).
提示: Does P/B contradict RIM.
出处: prbench:a7547bde6081d65475eb57d5 | 话题: Accounting & Financial Statement Analysis

## FIN-0851 [必须]
判据: The response applies a conversion ratio of 1 ADR = 5 ordinary shares to calculate ADR-equivalent per ordinary share as $37.00 ($185 ÷ 5).
提示: Prompt specifies 1:5 ratio; correct application is essential for arbitrage.
出处: prbench:a7547bde6081d65475eb57d5 | 话题: Accounting & Financial Statement Analysis

## FIN-0852 [必须]
判据: The response calculates net arbitrage after comprehensive costs (FX 20 bps, brokerage 15 bps, conversion 10 bps, Taiwan tax 30 bps, spreads 25 bps, frictions 50-100 bps (including other general costs, e.g., brokerage, conversion, Taiwan tax, spreads)), yielding net 1,960-2,110 bps (19.6%-21.1%).
提示: Realistic profit estimation requires systematic cost accounting beyond FX.
出处: prbench:a7547bde6081d65475eb57d5 | 话题: Accounting & Financial Statement Analysis

## FIN-0853 [必须]
判据: The response states that storage costs generally reduce hedging effectiveness across commodities.
提示: Addresses logistical risk factors.
出处: prbench:a8c848fa8c213861194291be | 话题: Investment Strategy & Portfolio Design

## FIN-0854 [必须]
判据: The response states that agriculture fails as a hedge when inflation is unrelated to food prices.
提示: Explains why agricultural hedges are inconsistent.
出处: prbench:a8c848fa8c213861194291be | 话题: Investment Strategy & Portfolio Design

## FIN-0855 [负面]
判据: The response incorrectly presents commodity investing as foolproof inflation protection.
提示: Dangerous oversimplification that could mislead investors by ignoring the conditional nature of hedge effectiveness.
出处: prbench:a8c848fa8c213861194291be | 话题: Investment Strategy & Portfolio Design

## FIN-0856 [建议]
判据: The response notes that storage costs for metals are relatively low compared to those of other commodities.
提示: Differentiates metals from perishable commodities.
出处: prbench:a8c848fa8c213861194291be | 话题: Investment Strategy & Portfolio Design

## FIN-0857 [必须]
判据: The response explains how agricultural supply shocks (e.g., drought, crop failure) translate into inflationary pressures on consumers.
提示: Connects agriculture supply shocks to inflation.
出处: prbench:a8c848fa8c213861194291be | 话题: Investment Strategy & Portfolio Design

## FIN-0858 [必须]
判据: The response explains why energy commodities can directly impact headline inflation numbers (e.g., high CPI weight or pass-through of energy costs).
提示: Tests understanding of economic mechanisms.
出处: prbench:a8c848fa8c213861194291be | 话题: Investment Strategy & Portfolio Design

## FIN-0859 [负面]
判据: The response incorrectly suggests that all commodities move together during inflationary periods.
提示: Serious misconception that ignores sector-specific dynamics and undermines hedge strategy.
出处: prbench:a8c848fa8c213861194291be | 话题: Investment Strategy & Portfolio Design

## FIN-0860 [必须]
判据: The response states that energy is a strong hedge during demand-driven inflation (e.g., growth booms).
提示: Clarifies conditions where energy correlates positively with inflation.
出处: prbench:a8c848fa8c213861194291be | 话题: Investment Strategy & Portfolio Design

## FIN-0861 [必须]
判据: The response states that commodities hedge better during demand-pull inflation than during cost-push inflation.
提示: Requires precise linkage of inflation type to hedge effectiveness.
出处: prbench:a8c848fa8c213861194291be | 话题: Investment Strategy & Portfolio Design

## FIN-0862 [必须]
判据: The response states that gold is a weak hedge against short-term consumer price spikes.
提示: Checks weak short-term inflation-gold relation.
出处: prbench:a8c848fa8c213861194291be | 话题: Investment Strategy & Portfolio Design

## FIN-0863 [负面]
判据: The response incorrectly recommends withdrawing from a Roth 401(k) as the preferred financing option for accessing the needed $50,000-$60,000 investment capital.
提示: ROTH 401k early withdrawal would trigger taxes and penalties, while cash-out refinancing offers lower-cost capital and preserves retirement savings. This represents fundamentally flawed financial advice.
出处: prbench:a8ea4dc9d68192216b6391cc | 话题: Wealth Management, Financial Planning & Advice

## FIN-0864 [必须]
判据: The response states that non-residents in Colombia generally cannot get access to local mortgages.
提示: This is a criterion that clarifies the point around the feasibility of financing.
出处: prbench:a8ea4dc9d68192216b6391cc | 话题: Wealth Management, Financial Planning & Advice

## FIN-0865 [必须]
判据: The response correctly states that a sale enables the GP to crystallize carry without waiting for future unrealized profits.
提示: Tests if immediate carry realization from sale is explained cleanly, avoiding any mixing with deferred events.
出处: prbench:a9e830a773e2a8621d65bb03 | 话题: Alternative Investments & Private Markets

## FIN-0866 [负面]
判据: The response states that holding a minority stake gives the fund control over exit timings.
提示: Any such claim is a critical factual error.
出处: prbench:a9e830a773e2a8621d65bb03 | 话题: Alternative Investments & Private Markets

## FIN-0867 [必须]
判据: The response states that a roll in which the second exit happens after 2 months will often delay the fund’s IRR.
提示: Ensures response clearly states the implications on IRR if the investment is held longer by rolling.
出处: prbench:a9e830a773e2a8621d65bb03 | 话题: Alternative Investments & Private Markets

## FIN-0868 [必须]
判据: The response states that an all-cash transaction increases short-term IRR for the fund.
提示: This will ensure the reponse focuses on how fast selling boosts the reported IRR for the fund.
出处: prbench:a9e830a773e2a8621d65bb03 | 话题: Alternative Investments & Private Markets

## FIN-0869 [必须]
判据: The response acknowledges that an all-cash transaction allows LPs to maximize immediate DPI.
提示: Isloates clarity around tradeoff in liquidity timing, without blending other goals or metrics, forcing explicit analysis of DPI.
出处: prbench:a9e830a773e2a8621d65bb03 | 话题: Alternative Investments & Private Markets

## FIN-0870 [必须]
判据: Response states the loans' accounting classification (HFI, HFS, FV option) determines how market value changes are recognized.
提示: Classification drives measurement and reporting rules.
出处: prbench:ab5d5685b57d60f47e4e0d51 | 话题: Accounting & Financial Statement Analysis

## FIN-0871 [建议]
判据: Response states that unrealized fair value changes on FVOCI instruments do not affect net income.
提示: Recognition that FVOCI gains/losses bypass earnings.
出处: prbench:ab5d5685b57d60f47e4e0d51 | 话题: Accounting & Financial Statement Analysis

## FIN-0872 [建议]
判据: Response states that unrealized fair value changes on FVOCI instruments are recorded in other comprehensive income (OCI).
提示: Proper treatment of OCI and distinction from P&L.
出处: prbench:ab5d5685b57d60f47e4e0d51 | 话题: Accounting & Financial Statement Analysis

## FIN-0873 [必须]
判据: Response warns against double-counting risk (e.g., by applying both fair value markdowns and CECL allowance increases for the same exposure).
提示: Prevents overstating losses and misrepresenting financial performance.
出处: prbench:ab5d5685b57d60f47e4e0d51 | 话题: Accounting & Financial Statement Analysis

## FIN-0874 [必须]
判据: Response states that net income flows into retained earnings on the balance sheet.
提示: Tests understanding of basic accounting flow from P&L to equity, independent of CECL or FV adjustments.
出处: prbench:ab5d5685b57d60f47e4e0d51 | 话题: Accounting & Financial Statement Analysis

## FIN-0875 [必须]
判据: Response explains that fair value declines do not hit earnings for amortized cost (HFI) loans unless expected credit losses increase.
提示: Ensure correct GAAP treatment of performing loans.
出处: prbench:ab5d5685b57d60f47e4e0d51 | 话题: Accounting & Financial Statement Analysis

## FIN-0876 [必须]
判据: Response states that CECL must incorporate forecasted macro conditions (e.g., higher cap rate, weaker collateral values) even without impairment.
提示: Captures forwad-looking loss estimation requirement.
出处: prbench:ab5d5685b57d60f47e4e0d51 | 话题: Accounting & Financial Statement Analysis

## FIN-0877 [建议]
判据: Response explains how increases in the CECL allowance reduce net income through provision expense in the income statement.
提示: Links credit loss measurement to earnings.
出处: prbench:ab5d5685b57d60f47e4e0d51 | 话题: Accounting & Financial Statement Analysis

## FIN-0878 [必须]
判据: The response correctly calculates the target return rate of 6.60%.
提示: correct use of formula
出处: prbench:acc49da196b882669f38211e | 话题: Wealth Management, Financial Planning & Advice

## FIN-0879 [负面]
判据: The response adds a lump sum value of 15 years' contributions, $750,000, to the initial investment.
提示: time value of money
出处: prbench:acc49da196b882669f38211e | 话题: Wealth Management, Financial Planning & Advice

## FIN-0880 [必须]
判据: The response correctly recognizes that under IFRS 9 (B6.5.13), a USD-functional intermediate entity doesn't prevent designation because consolidated exposure is determined at the group level, not by intermediate functional currencies.
提示: Understanding how functional currency layers affect consolidated hedge accounting is critical to answering correctly.
出处: prbench:aec8942a8cf9cb1828362181 | 话题: Accounting & Financial Statement Analysis

## FIN-0881 [必须]
判据: The response mentions the economic relationship requirement under IFRS 9 for hedge effectiveness (i.e., the hedged item and hedging instrument generally move in opposite directions).
提示: IFRS 9 requires demonstrating economic relationship between hedging instrument and hedged item
出处: prbench:aec8942a8cf9cb1828362181 | 话题: Accounting & Financial Statement Analysis

## FIN-0882 [必须]
判据: The response concludes that a EUR-functional holdco can designate USD/JPY forwards to hedge consolidated USD/JPY exposure when an intervening USD-functional entity exists.
提示: This is the primary question asked and requires understanding IFRS 9 hedge accounting at consolidated level.
出处: prbench:aec8942a8cf9cb1828362181 | 话题: Accounting & Financial Statement Analysis

## FIN-0883 [必须]
判据: The response addresses the fact that the CTA is not recycled when 25% NCI is sold while retaining control.
提示: This is the second explicit question and requires precise IAS 21.48-48A interpretation.
出处: prbench:aec8942a8cf9cb1828362181 | 话题: Accounting & Financial Statement Analysis

## FIN-0884 [必须]
判据: The response states that CTA being fully recycled to P&L violates IAS 21.48A, which only requires proportionate recycling for the NCI portion.
提示: This violates IAS 21.48A which only requires proportionate recycling for NCI portion
出处: prbench:aec8942a8cf9cb1828362181 | 话题: Accounting & Financial Statement Analysis

## FIN-0885 [必须]
判据: The response correctly identifies the hedged risk for a net investment hedge as the difference between the ultimate parent's functional currency and the foreign operation's currency (i.e., EUR, JPY).
提示: This is to identify the hedged risk pair at consolidated level.
出处: prbench:aec8942a8cf9cb1828362181 | 话题: Accounting & Financial Statement Analysis

## FIN-0886 [建议]
判据: The response mentions that the effective portion of a net investment hedge is recognized in OCI/FCTR.
提示: Understanding presentation impact helps assess practical implications
出处: prbench:aec8942a8cf9cb1828362181 | 话题: Accounting & Financial Statement Analysis

## FIN-0887 [必须]
判据: The response identifies that a USD/JPY forward can be designated against its exposure (i.e., by accepting EUR/USD basis ineffectiveness and explicitly scoping the hedge to the USD parent's USD/JPY net investment).
提示: This gives explanation to the USD/JPY forward against the exposure.
出处: prbench:aec8942a8cf9cb1828362181 | 话题: Accounting & Financial Statement Analysis

## FIN-0888 [必须]
判据: The response states the correct formula: tracking error = portfolio weight * active volatility.
提示: Core underlying concept of the prompt.
出处: prbench:b108ae8a235db31678e3062a | 话题: Investment Strategy & Portfolio Design

## FIN-0889 [必须]
判据: The response states that expected gross edge must be at least equal to total trading costs to break even.
提示: Checks if response compares expected profit per event with all in costs.
出处: prbench:b108ae8a235db31678e3062a | 话题: Investment Strategy & Portfolio Design

## FIN-0890 [必须]
判据: The response explicitly states maximum drawdown is path-dependent: the largest peak-to-trough drop over the period, different from the 95% worst-case one-year loss.
提示: avoid mixing up two concepts.
出处: prbench:b14d78d6a5e4e16b9750d555 | 话题: Risk Management & Stress Testing

## FIN-0891 [必须]
判据: The response correctly calculates post outflow liquidity: 35% - 8% = 27%.
提示: Checks for post outflow liquidity calculation.
出处: prbench:b14d78d6a5e4e16b9750d555 | 话题: Risk Management & Stress Testing

## FIN-0892 [必须]
判据: The response correctly calculates the coverage ratio: 35% / 8% = 4.4x coverage.
提示: checks for coverage ratio accuracy.
出处: prbench:b14d78d6a5e4e16b9750d555 | 话题: Risk Management & Stress Testing

## FIN-0893 [必须]
判据: The response distinguishes refundable credits from nonrefundable or transferable credits (e.g., refundable = excess returned, nonrefundable = capped at liability, transferable = can be sold).
提示: Misclassifying credits leads to incorrect ETR modeling and erroneous conclusions about after-tax profitability.
出处: prbench:b417e5be58dd715ad45606e5 | 话题: Taxation & Cross-Border Structuring

## FIN-0894 [必须]
判据: The response explains the Pillar Two deferred tax timing effect on the GloBE ETR (e.g., nonrefundable credits can depress the GloBE ETR and increase top-ups, while qualified refundable credits are treated more favorably).
提示: Misclassifying credits leads to incorrect ETR modeling and erroneous conclusions about after-tax profitability.
出处: prbench:b417e5be58dd715ad45606e5 | 话题: Taxation & Cross-Border Structuring

## FIN-0895 [必须]
判据: The response distinguishes consolidated earnings from parent-level free cash flow (e.g., Consolidated earnings = total net income of parent+subsidiaries; parent-level free cash flow = net cash post-capex for parent company only).
提示: Investors are paid with parent cash, not consolidated accounting earnings, so mobility clarity is essential.
出处: prbench:b417e5be58dd715ad45606e5 | 话题: Taxation & Cross-Border Structuring

## FIN-0896 [必须]
判据: Defines BBB sub-notch thresholds numerically (e.g., BBB+: FFO/ND >32%, ND/EBITDA <2.3×; BBB: 25-32%, 2.3-3.0×; BBB-: 20-25%, 3.0-3.5×).
提示: Tests internal numerical consistency
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0897 [负面]
判据: Uses simplified downgrade formula instead of matrix multiplication (e.g., incorrectly uses P = 1 - (stable)^5 instead of T^5).
提示: Oversimplified probability formulas ignore rating migration paths and produce incorrect risk assessments.
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0898 [负面]
判据: Maintains constant interest rates in the austere scenario (e.g., uses 4.5% throughout instead of applying the 6.0% stressed rate).
提示: Missing the 150bps stress invalidates the entire austere scenario analysis.
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0899 [必须]
判据: Specifies covenant thresholds and calculates headroom annually (e.g., Net Debt/EBITDA covenant 3.5×, Y3 austere actual 3.2×, headroom 0.3× or €285m EBITDA cushion).
提示: Requires quantitative governance design
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0900 [必须]
判据: Calculates debt tax shields annually (e.g., Y3 austere: Interest €180m × 25% tax rate = €45m tax benefit, NPV at 6% = €640m).
提示: Tests rate-risk modeling
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0901 [必须]
判据: Calculates S&P FFO as cash flow from operations before working capital changes with specific adjustments (e.g., Y1 FFO = CFO pre-WC €750m + lease adjustments €30m - cash taxes €180m = €600m).
提示: Forces explicit rating-metric derivation.
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0902 [必须]
判据: Calculates 5-year downgrade probability using matrix multiplication T^5 for each scenario (e.g., Benign: 12% probability BBB→<BBB; Austere: 38% probability).
提示: Turns qualitative labels into measurable criteria.
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0903 [负面]
判据: Uses EBITDA-based FFO shortcuts instead of CFO-based calculations (e.g., incorrectly states FFO = EBITDA - taxes - capex).
提示: EBITDA-based FFO is wrong; S&P uses cash flow from operations with specific adjustments.
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0904 [必须]
判据: Calculates interest coverage as EBITDA/Cash Interest for Y1-Y5 in both scenarios (e.g., Benign: Y1 8.5×, Y3 9.2×; Austere: Y1 6.8×, Y3 4.5× after +150bps).
提示: Enforces quantitative time-series compliance check
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0905 [建议]
判据: Quantifies liquidity reserves including RCF and minimum cash (e.g., €500m undrawn RCF + €150m minimum cash = €650m liquidity buffer).
提示: Adds realistic covenant and funding detail.
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0906 [必须]
判据: Calculates WACC using market weights and tax-adjusted debt cost (e.g., Y1: E/V 65% × 9.5% + D/V 35% × 4.5% × (1-25%) = 7.36%).
提示: Requires full capital-cost modeling
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0907 [负面]
判据: Applies tax adjustment to cost of equity in WACC (e.g., incorrectly uses CoE × (1-tax) instead of CoE alone).
提示: Only debt cost receives tax adjustment in WACC; applying it to equity cost is an error.
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0908 [建议]
判据: Calculates EPS accretion/dilution including buyback effects (e.g., Y3 benign: EPS €4.20 (+15% vs base); austere: €2.80 (-23% vs base)).
提示: Converts qualitative intent into measurable constraint.
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0909 [必须]
判据: Shows WACC evolution Y1-Y5 for both scenarios (e.g., Benign: 7.4% → 6.8% as leverage decreases; Austere: 7.4% → 8.2% as risk premiums widen).
提示: Tests numeric precision
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0910 [必须]
判据: Calculates S&P-adjusted net debt by adding 50% of hybrid instruments classified as equity under IFRS (e.g., IFRS net debt €2,900m + [€250m hybrid × 50%] = €3,025m adjusted).
提示: Requires concrete math
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0911 [必须]
判据: Applies the austere scenario's 10% EBITDA decline by Y3 with an explicit path (e.g., Y1 €950m, Y2 €902m [-5%], Y3 €855m [-10% cumulative]).
提示: Tests full rating alignment
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0912 [必须]
判据: Calculates equity value using DCF with scenario-specific WACC (e.g., Benign: €4.2bn using 6.8% terminal WACC; Austere: €2.8bn using 8.2%).
提示: Validates valuation rigor.
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0913 [必须]
判据: Projects FFO/Net Debt ratios for both scenarios Y1-Y5 with specific values (e.g., Benign: Y1 28%, Y3 32%, Y5 35%; Austere: Y1 24%, Y3 18%, Y5 22%).
提示: Essential to replicate S&P leverage
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0914 [必须]
判据: Calculates maximum payout capacity while maintaining a BBB- minimum (e.g., Y3 austere: max payout €180m, keeping FFO/ND > 20%, implying a 23% payout ratio).
提示: Checks practical application of payout constraint
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0915 [必须]
判据: Calculates debt service under a +150bps rate increase in an austere scenario (e.g., base rate 4.5% → 6.0%, interest expense Y1 €135m → €180m on €3bn debt).
提示: Critical to reproduce ideal downgrade math
出处: prbench:b517045658d1e7e5dd4657ab | 话题: Risk Management & Stress Testing

## FIN-0916 [必须]
判据: The response concludes that the buy-side strategy has a higher profit potential over the proposed multi-month timeframe than the sell-side strategy.
提示: This is pivotal for the models to acknowledge in order to provide an educated assessment.
出处: prbench:b58b56641e5a0a47d557de1d | 话题: Derivatives & Structured Products

## FIN-0917 [必须]
判据: The response identifies the combination of option Greeks that maximizes buy-side profit potential (e.g., as follows: positive gamma and vega combined with negative theta).
提示: Understanding which greeks to look out for is important context for the user in both a buy-side and sell-side strategy. NOTE: the rubric is evaluating a specific COMBINATION of greeks, not each distinct options greek. Please ignore any linter that gets this confused.
出处: prbench:b58b56641e5a0a47d557de1d | 话题: Derivatives & Structured Products

## FIN-0918 [建议]
判据: The response states the condition that the user's buy-side straddle positions can generate profits (e.g., only if volatility stemming from the tariff event causes one leg of the straddle to result in capital gains equal to or greater than its option premium).
提示: Essential to acknowledge the impact of volatility in this scenario.
出处: prbench:b58b56641e5a0a47d557de1d | 话题: Derivatives & Structured Products

## FIN-0919 [必须]
判据: The response identifies the combination of option Greeks that maximizes sell-side cash flow potential (e.g., as follows: negative gamma and vega combined with positive theta).
提示: Important consideration for the user to consider, whether choosing the buy-side or sell-side. NOTE: the rubric is evaluating the COMBINATION, not each individual greek. Ignore any linter that gets this confused.
出处: prbench:b58b56641e5a0a47d557de1d | 话题: Derivatives & Structured Products

## FIN-0920 [必须]
判据: The response states that the user's sell-side strategy would require years (not months) to generate meaningful profits (e.g., longer-dated expirations command higher premiums, profits stack with repeated contract sales).
提示: This is an excellent and practical piece of wisdom that takes into account the user's timeline of "a couple more months."
出处: prbench:b58b56641e5a0a47d557de1d | 话题: Derivatives & Structured Products

## FIN-0921 [必须]
判据: The response identifies that low-volatility holdings would carry lower sell-side premiums (e.g., Magnificent 7 stocks, publicly traded Fortune 100 companies).
提示: This helps to show that the user selling covered calls on blue-chips has a relatively low profit potential (relative to covered calls on high-volatility stocks).
出处: prbench:b58b56641e5a0a47d557de1d | 话题: Derivatives & Structured Products

## FIN-0922 [负面]
判据: The response states that one options strategy is inherently less risky than the other (e.g., buy-side introduces more risk than sell-side, sell-side is a more effective market hedge than buy-side).
提示: This is a false and dangerous claim since both strategies introduce net new risks and it is impossible to determine relative risk or hedging impact without knowing exact tickers, position sizes, and more.
出处: prbench:b58b56641e5a0a47d557de1d | 话题: Derivatives & Structured Products

## FIN-0923 [必须]
判据: The response explains that foreign taxes on the parent's income cannot be credited against a UK CFC charge on a subsidiary's profits.
提示: Tests a crucial, technical rule in FTC mechanics.
出处: prbench:b595dc737efd14f628cff4b6 | 话题: Taxation & Cross-Border Structuring

## FIN-0924 [必须]
判据: The response explains the need to make comparability adjustments to the selected comparables (e.g., risk adjustments, working capital adjustments).
提示: Demonstrates an understanding of foundational transfer pricing principles.
出处: prbench:b595dc737efd14f628cff4b6 | 话题: Taxation & Cross-Border Structuring

## FIN-0925 [建议]
判据: The response cites TIOPA 2010 Part 2, which identifies that the £207k US penalty is not creditable against UK corporation tax.
提示: Confirms a basic principle of tax creditability with authority.
出处: prbench:b595dc737efd14f628cff4b6 | 话题: Taxation & Cross-Border Structuring

## FIN-0926 [必须]
判据: The response discusses the transfer pricing methodology of using comparables to establish an arm's length price.
提示: Demonstrates an understanding of foundational transfer pricing principles.
出处: prbench:b595dc737efd14f628cff4b6 | 话题: Taxation & Cross-Border Structuring

## FIN-0927 [必须]
判据: The response determines the US subsidiary's eligibility for the tax mismatch exemption by comparing its effective tax rate against the 18.75% threshold.
提示: Determines the primary CFC exemption eligibility.
出处: prbench:b595dc737efd14f628cff4b6 | 话题: Taxation & Cross-Border Structuring

## FIN-0928 [必须]
判据: The response explains that entity-level exemptions are applied before the UK CFC charge gateway tests.
提示: Demonstrates expert knowledge of CFC procedural ordering.
出处: prbench:b595dc737efd14f628cff4b6 | 话题: Taxation & Cross-Border Structuring

## FIN-0929 [必须]
判据: The response presents the final net UK tax liability on the £5.525m royalty after applying the £829k foreign tax credit, showing a result of approximately £552,000.
提示: Tests the fundamental double taxation relief calculation.
出处: prbench:b595dc737efd14f628cff4b6 | 话题: Taxation & Cross-Border Structuring

## FIN-0930 [必须]
判据: The response calculates that the California tax creates orphaned credits, showing an uncreditable amount of approximately £1.55m.
提示: Quantifies the final, unrecoverable cost of double taxation.
出处: prbench:b595dc737efd14f628cff4b6 | 话题: Taxation & Cross-Border Structuring

## FIN-0931 [必须]
判据: The response's analysis of the California tax issue includes a discussion of whether a Permanent Establishment (PE) is created.
提示: Tests a critical, foundational step in any treaty-based analysis.
出处: prbench:b595dc737efd14f628cff4b6 | 话题: Taxation & Cross-Border Structuring

## FIN-0932 [负面]
判据: Response states the IP sale price is the same as the CCA buy-in payment (i.e., the buy-in is the same as the sale consideration).
提示: This is a major and misleading error.
出处: prbench:b5c48f77f3f9f7cd6155db26 | 话题: Taxation & Cross-Border Structuring

## FIN-0933 [必须]
判据: Response specifies that the buy-in valuation should use a post-tax Discounted Cash Flow model (i.e., cash flows are modeled after accounting for corporate taxes).
提示: This is a standard valuation convention.
出处: prbench:b5c48f77f3f9f7cd6155db26 | 话题: Taxation & Cross-Border Structuring

## FIN-0934 [必须]
判据: Response specifies Swiss thin-cap testing is based on the asset's tax book value (i.e., the debt capacity is determined by the value on the Swiss tax balance sheet).
提示: This tests specific Swiss tax mechanics.
出处: prbench:b5c48f77f3f9f7cd6155db26 | 话题: Taxation & Cross-Border Structuring

## FIN-0935 [必须]
判据: Response describes the CCA buy-in payment as a separate transaction from the IP sale (i.e., the buy-in is a distinct payment for joining the CCA).
提示: This is a fundamental structural point.
出处: prbench:b5c48f77f3f9f7cd6155db26 | 话题: Taxation & Cross-Border Structuring

## FIN-0936 [必须]
判据: Response notes the UK founder has no immediate personal tax from the IP sale (i.e., the company's asset sale does not trigger a direct tax charge for the shareholder).
提示: This tests a critical misunderstanding.
出处: prbench:b5c48f77f3f9f7cd6155db26 | 话题: Taxation & Cross-Border Structuring

## FIN-0937 [建议]
判据: Response states the Relief from Royalty method requires a benchmark of third-party license agreements (i.e., the royalty rate is based on comparable uncontrolled licenses).
提示: This is a required step for the RFR method.
出处: prbench:b5c48f77f3f9f7cd6155db26 | 话题: Taxation & Cross-Border Structuring

## FIN-0938 [建议]
判据: Response suggests using a multi-factor model for Reasonably Anticipated Benefits (e.g., RAB is based on a weighted average of projected sales, weighted average of projected users).
提示: This shows a more sophisticated approach to RAB.
出处: prbench:b5c48f77f3f9f7cd6155db26 | 话题: Taxation & Cross-Border Structuring

## FIN-0939 [必须]
判据: The response verifies the forward rate using covered interest rate parity (e.g., by calculating the theoretical forward as spot × (1 + r_USD × T) / (1 + r_EUR × T), comparing to the given 1.1015 forward, or explicitly stating interest rate assumptions consistent with the forward premium).
提示: The forward premium must be justified by interest rate differentials; using an unexplained forward rate without verification is incomplete.
出处: prbench:b607ce69809c42c4086f7369 | 话题: International Finance & FX Hedging

## FIN-0940 [负面]
判据: The response calculates shortfall probability by comparing scenarios against a $48.5m threshold without using proper probability distributions (e.g., simply counting how many of the 5 scenarios fall short).
提示: Scenario counting is not probability calculation; proper statistical methods using volatility are required.
出处: prbench:b607ce69809c42c4086f7369 | 话题: International Finance & FX Hedging

## FIN-0941 [负面]
判据: The response calculates zero-cost collar strikes using arbitrary or unrealistic spreads (e.g., put at 1.00, call at 1.20) without using option pricing based on the 8.5% volatility or validating these strikes are market-consistent.
提示: Strikes must be derived from option pricing models using provided volatility; arbitrary strikes indicate lack of technical rigor.
出处: prbench:b607ce69809c42c4086f7369 | 话题: International Finance & FX Hedging

## FIN-0942 [必须]
判据: The response computes expected USD proceeds for all four strategies (e.g., 100% forward, 100% collar, 50% collar, unhedged; forward yields $49.57m expected, unhedged yields $48.60m expected).
提示: Expected value calculations are required deliverables for comparing strategies.
出处: prbench:b607ce69809c42c4086f7369 | 话题: International Finance & FX Hedging

## FIN-0943 [必须]
判据: The response verifies that the recommended zero-cost collar put strike is above the 1.0778 breakeven threshold (e.g., by explicitly stating its implication for shortfall probability).
提示: If put strike is below breakeven, the hedge fails the primary objective; this must be explicitly verified.
出处: prbench:b607ce69809c42c4086f7369 | 话题: International Finance & FX Hedging

## FIN-0944 [必须]
判据: The response calculates the probability of falling short of $48.5m under each strategy using the 8.5% volatility to derive a probability distribution (e.g., using lognormal distribution or Monte Carlo).
提示: Probability calculation is essential to verify the 10% constraint and requires proper statistical methodology.
出处: prbench:b607ce69809c42c4086f7369 | 话题: International Finance & FX Hedging

## FIN-0945 [必须]
判据: The response acknowledges the FX volatility skew when pricing the zero-cost collar (e.g., implied vol surface interpolation, smile curvature bias adjustments).
提示: Using a flat ATM volatility across all strikes ignores the volatility smile/skew that materially affects option pricing and collar strike calculations.
出处: prbench:b607ce69809c42c4086f7369 | 话题: International Finance & FX Hedging

## FIN-0946 [必须]
判据: The response incorporates volatility surface skew/smile into any option-based hedging proposal.
提示: Tests sophisticated volatility modeling considerations.
出处: prbench:b7038ed520aae6663f83ba12 | 话题: Derivatives & Structured Products

## FIN-0947 [建议]
判据: The response recalculates CVA with deteriorating counterparty credit (e.g., declining capital adequacy ratios, increasing non-performing loans, weakening profitability).
提示: Tests credit risk quantification under changing market conditions.
出处: prbench:b7038ed520aae6663f83ba12 | 话题: Derivatives & Structured Products

## FIN-0948 [必须]
判据: The response recalculates CVA directionally using CVA = LGD x integral of EPE(t) x PD(t) dt under updated exposure dynamics.
提示: Tests credit risk quantification under changing market conditions.
出处: prbench:b7038ed520aae6663f83ba12 | 话题: Derivatives & Structured Products

## FIN-0949 [必须]
判据: The response identifies how exposure concentrates in the breached S&P underlying versus the intact barriers (e.g., EUROSTOXX and Nikkei).
提示: Tests understanding of asymmetric risk distribution after partial barrier breach.
出处: prbench:b7038ed520aae6663f83ba12 | 话题: Derivatives & Structured Products

## FIN-0950 [必须]
判据: The response updates correlation modeling using a time-varying approach (e.g., DCC-GARCH, regime-switching, or high-frequency realized measures).
提示: Tests practical model implementation knowledge.
出处: prbench:b7038ed520aae6663f83ba12 | 话题: Derivatives & Structured Products

## FIN-0951 [必须]
判据: The response directionally analyses delta behavior under autocall conditions post-breach (e.g., the note transforms from a complex structured product into a simpler path-dependent vanilla option, and the note is automatically redeemed).
提示: Tests understanding of non-linear risk behavior while allowing for various analytical approaches.
出处: prbench:b7038ed520aae6663f83ba12 | 话题: Derivatives & Structured Products

## FIN-0952 [必须]
判据: The response quantifies delta’s change as a function of distance to barrier (i.e., down-and-in put, down-and-out put).
提示: Tests understanding of non-linear risk behavior while allowing for various analytical approaches.
出处: prbench:b7038ed520aae6663f83ba12 | 话题: Derivatives & Structured Products

## FIN-0953 [必须]
判据: The response analyzes the impact of the S&P barrier breach on the note's Greeks (e.g., delta, own-gamma, cross-gamma, vega) with only 8 observations remaining.
提示: Tests sophisticated understanding of how barrier breaches affect risk sensitivities.
出处: prbench:b7038ed520aae6663f83ba12 | 话题: Derivatives & Structured Products

## FIN-0954 [必须]
判据: The response notes that missed coupons are paid retroactively if all indices recover above initial levels.
提示: Tests the specific understanding of memory feature mechanics separately from general product terms.
出处: prbench:b7038ed520aae6663f83ba12 | 话题: Derivatives & Structured Products

## FIN-0955 [必须]
判据: The response explains that the memory feature affects valuation near observation dates.
提示: Tests the specific understanding of memory feature mechanics separately from general product terms.
出处: prbench:b7038ed520aae6663f83ba12 | 话题: Derivatives & Structured Products

## FIN-0956 [建议]
判据: The response lists all five functions of the OECD DEMPE framework: Development, Enhancement, Maintenance, Protection, and Exploitation.
提示: Correctly identifying all five DEMPE functions.
出处: prbench:b7de65a5418d75b61e05545d | 话题: Taxation & Cross-Border Structuring

## FIN-0957 [必须]
判据: The response identifies the specific primary consequence of an ATAD 2 Deduction/No Inclusion (D/NI) mismatch for the Dutch-to-Ireland loan as the denial of the interest deduction in the payer jurisdiction (Netherlands).
提示: Identifying the specific consequence.
出处: prbench:b7de65a5418d75b61e05545d | 话题: Taxation & Cross-Border Structuring

## FIN-0958 [必须]
判据: The response calculates a jurisdictional Effective Tax Rate under Pillar Two rules by dividing Adjusted Covered Taxes (income taxes recorded in financial accounts, adjusted per GloBE rules) by Net GloBE Income (financial accounting net income/loss adjusted per GloBE rules) for at least one entity.
提示: This tests the core technical application.
出处: prbench:b7de65a5418d75b61e05545d | 话题: Taxation & Cross-Border Structuring

## FIN-0959 [必须]
判据: The response states that Ireland's interest limitation rule restricts net deductible interest expense to 30% of EBITDA.
提示: Local rule impacting the structure.
出处: prbench:b7de65a5418d75b61e05545d | 话题: Taxation & Cross-Border Structuring

## FIN-0960 [必须]
判据: The response provides the correct formula for Effective Tax Rate as Total Income Tax Expense (Current + Deferred) / Profit Before Tax.
提示: Correct ETR formula.
出处: prbench:b7de65a5418d75b61e05545d | 话题: Taxation & Cross-Border Structuring

## FIN-0961 [建议]
判据: The response correctly states the 2025 Ireland corporate tax rate is 12.5%.
提示: Basic factual data point.
出处: prbench:b7de65a5418d75b61e05545d | 话题: Taxation & Cross-Border Structuring

## FIN-0962 [必须]
判据: The response recognizes termination fees as an EBITDA-reducing integration cost.
提示: Need to model their explicit effect on returns.
出处: prbench:b8b37361ead260e052ea8a36 | 话题: Corporate Finance

## FIN-0963 [必须]
判据: The response recognises that existing GPO contracts run 18–24 months.
提示: ICs need cashflow timing detail, not just aggregate haircut.
出处: prbench:b8b37361ead260e052ea8a36 | 话题: Corporate Finance

## FIN-0964 [建议]
判据: The response demonstrates that the adjusted synergy profile is realistic by factoring in the profiles of external competitors (e.g., HCA, Tenet, CHS, UHS).
提示: Valuable insight.
出处: prbench:b8b37361ead260e052ea8a36 | 话题: Corporate Finance

## FIN-0965 [必须]
判据: The response quantifies termination fees' effect on IRR, not just reclassification language (e.g., paying $15M in Year 1 reduces IRR from 12.0% to 11.2% (−80 bps)).
提示: Need to model their explicit effect on returns.
出处: prbench:b8b37361ead260e052ea8a36 | 话题: Corporate Finance

## FIN-0966 [必须]
判据: The response defines the liquidity coverage ratio correctly by stating: Liquidity coverage ratio = high-quality liquid assets / net 30-day cash outflows.
提示: Checks if the response use the right formula.
出处: prbench:b97f18fdf5f65cbc49676d32 | 话题: Risk Management & Stress Testing

## FIN-0967 [必须]
判据: The response recalculates high quality liquid assets after the shock.
提示: Checks if response treat what counts as liquid assets correctly.
出处: prbench:b97f18fdf5f65cbc49676d32 | 话题: Risk Management & Stress Testing

## FIN-0968 [必须]
判据: The response explicitly says pledged or reused assets are not counted as available liquid assets.
提示: Prevents double counting.
出处: prbench:b97f18fdf5f65cbc49676d32 | 话题: Risk Management & Stress Testing

## FIN-0969 [负面]
判据: The response contains internally contradictory financial statements (such as stating different conversion rates, timeline assumptions, or margin calculations within the same analysis).
提示: Inconsistent assumptions undermine analytical credibility and could mislead decision-makers.
出处: prbench:b9d96a1e9c12d148a3261c86 | 话题: Corporate Finance

## FIN-0970 [必须]
判据: The response correctly calculates the revenue synergy opportunity as $30 million ARR (500 customers × $60,000).
提示: This is an important intermediary step that feeds the correct downstream PV and EBITDA calculations.
出处: prbench:b9d96a1e9c12d148a3261c86 | 话题: Corporate Finance

## FIN-0971 [负面]
判据: The response uses incorrect financial multiples or benchmarks not provided in the prompt (such as applying different WACC rates or tax assumptions).
提示: Using wrong parameters undermines analysis credibility but doesn't fundamentally break the methodology.
出处: prbench:b9d96a1e9c12d148a3261c86 | 话题: Corporate Finance

## FIN-0972 [必须]
判据: The response applies the provided 10% WACC to calculate the present value or valuation impact of the revenue synergies.
提示: This is an important intermediate step for calculating the PV of revenue synergies.
出处: prbench:b9d96a1e9c12d148a3261c86 | 话题: Corporate Finance

## FIN-0973 [必须]
判据: The response correctly calculates the purchase price multiple as 12x EBITDA.
提示: This is a critical step for assessing whether the deal is accretive or dilutive.
出处: prbench:b9d96a1e9c12d148a3261c86 | 话题: Corporate Finance

## FIN-0974 [必须]
判据: The response correctly classifies the 500-customer opportunity as a revenue synergy rather than a cost synergy.
提示: Proper synergy classification is essential for accurate M&A analysis and valuation methodology.
出处: prbench:b9d96a1e9c12d148a3261c86 | 话题: Corporate Finance

## FIN-0975 [负面]
判据: The response applies fundamentally incorrect financial methodology such as comparing pre-tax cash flows to after-tax multiples or using revenue multiples instead of EBITDA multiples without adjustment.
提示: Severe methodological errors could lead to dangerous investment decisions and demonstrates lack of basic financial competency.
出处: prbench:b9d96a1e9c12d148a3261c86 | 话题: Corporate Finance

## FIN-0976 [必须]
判据: The response demonstrates that the acquisition is value-creating through sound financial logic (such as NPV analysis or accretion metrics).
提示: The core conclusion about value creation must be supported by proper financial analysis.
出处: prbench:b9d96a1e9c12d148a3261c86 | 话题: Corporate Finance

## FIN-0977 [必须]
判据: The response applies the 30% corporate tax rate to calculate after-tax synergy benefits.
提示: Tax considerations materially impact the true value of synergies and deal economics.
出处: prbench:b9d96a1e9c12d148a3261c86 | 话题: Corporate Finance

## FIN-0978 [负面]
判据: The response applies inappropriate financial comparisons by mixing methodologies (such as comparing pre-tax metrics to post-tax benchmarks or applying consumer software multiples to enterprise software).
提示: Methodological inconsistencies can lead to incorrect valuation conclusions and poor investment decisions.
出处: prbench:b9d96a1e9c12d148a3261c86 | 话题: Corporate Finance

## FIN-0979 [建议]
判据: The response calculates the loss on the £150,000 Apple position as £30,000 by applying the 20% decline.
提示: Basic portfolio loss calculation explicitly requested.
出处: prbench:ba4a0ce2296616892a1dc813 | 话题: Risk Management & Stress Testing

## FIN-0980 [建议]
判据: The response calculates the post-scenario portfolio value as £380,000 by subtracting the £120,000 loss from the initial £500,000.
提示: Quantifies unhedged scenario outcome.
出处: prbench:ba4a0ce2296616892a1dc813 | 话题: Risk Management & Stress Testing

## FIN-0981 [建议]
判据: The response calculates the total expected portfolio loss as £120,000 by summing the four individual position losses.
提示: Aggregate risk assessment explicitly requested.
出处: prbench:ba4a0ce2296616892a1dc813 | 话题: Risk Management & Stress Testing

## FIN-0982 [必须]
判据: The response calculates that the £150,000 TSMC position represents 1,114 shares by dividing £150,000 by the stated $175 share price at the 1.30 exchange rate.
提示: Foundation for precise hedge contract sizing.
出处: prbench:ba4a0ce2296616892a1dc813 | 话题: Risk Management & Stress Testing

## FIN-0983 [建议]
判据: The response calculates that the £150,000 Apple position represents 867 shares by dividing £150,000 by the stated $225 share price at the 1.30 exchange rate.
提示: Foundation for precise hedge contract sizing.
出处: prbench:ba4a0ce2296616892a1dc813 | 话题: Risk Management & Stress Testing

## FIN-0984 [必须]
判据: The response calculates that the £100,000 Micron position represents 1,238 shares by dividing £100,000 by the stated $105 share price at the 1.30 exchange rate.
提示: Foundation for precise hedge contract sizing.
出处: prbench:ba4a0ce2296616892a1dc813 | 话题: Risk Management & Stress Testing

## FIN-0985 [必须]
判据: The response calculates a net outcome for at least one hedge by subtracting the stated upfront premium cost from its calculated gross payout.
提示: Net protection is true measure of hedge value.
出处: prbench:ba4a0ce2296616892a1dc813 | 话题: Risk Management & Stress Testing

## FIN-0986 [必须]
判据: The response quantifies TSMC's quarterly revenue impact by calculating $8bn as 40% of the stated $20bn quarterly revenue.
提示: Uses provided data for company-specific impact quantification.
出处: prbench:ba4a0ce2296616892a1dc813 | 话题: Risk Management & Stress Testing

## FIN-0987 [必须]
判据: The response calculates the total portfolio value in USD as $650,000 by applying the stated 1.30 GBP/USD exchange rate to the £500,000 portfolio.
提示: Currency conversion foundation for USD instrument sizing.
出处: prbench:ba4a0ce2296616892a1dc813 | 话题: Risk Management & Stress Testing

## FIN-0988 [必须]
判据: The response calculates the number of option contracts required for at least one position by dividing the number of shares held by 100 shares per contract.
提示: Core implementation detail explicitly requested.
出处: prbench:ba4a0ce2296616892a1dc813 | 话题: Risk Management & Stress Testing

## FIN-0989 [必须]
判据: The response calculates the hedge ratio (percentage of portfolio notional covered) for at least one proposed hedging strategy.
提示: Quantifies protection coverage level.
出处: prbench:ba4a0ce2296616892a1dc813 | 话题: Risk Management & Stress Testing

## FIN-0990 [建议]
判据: The response calculates the loss on the £100,000 Nvidia position as £20,000 by applying the 20% decline.
提示: Basic portfolio loss calculation explicitly requested.
出处: prbench:ba4a0ce2296616892a1dc813 | 话题: Risk Management & Stress Testing

## FIN-0991 [必须]
判据: The response quantifies Micron's quarterly revenue impact by calculating approximately $1.05bn as 25% of 60% of the stated $7bn quarterly revenue.
提示: Uses provided APAC exposure data for impact analysis.
出处: prbench:ba4a0ce2296616892a1dc813 | 话题: Risk Management & Stress Testing

## FIN-0992 [建议]
判据: The response calculates the loss on the £150,000 TSMC position as £45,000 by applying the 30% decline.
提示: Basic portfolio loss calculation explicitly requested.
出处: prbench:ba4a0ce2296616892a1dc813 | 话题: Risk Management & Stress Testing

## FIN-0993 [建议]
判据: The response calculates the loss on the £100,000 Micron position as £25,000 by applying the 25% decline.
提示: Basic portfolio loss calculation explicitly requested.
出处: prbench:ba4a0ce2296616892a1dc813 | 话题: Risk Management & Stress Testing

## FIN-0994 [建议]
判据: The response calculates that the £100,000 Nvidia position represents 1,040 shares by dividing £100,000 by the stated $125 share price at the 1.30 exchange rate.
提示: Foundation for precise hedge contract sizing.
出处: prbench:ba4a0ce2296616892a1dc813 | 话题: Risk Management & Stress Testing

## FIN-0995 [必须]
判据: The response describes pro-rata rights mechanics for existing holders; for example, for every old share, holders may buy 0.75 new shares to maintain the same percentage.
提示: Explaining how participation or non participation affects legacy ownership is vital for fairnes.
出处: prbench:ba626d238986994ead41cc11 | 话题: Corporate Finance

## FIN-0996 [必须]
判据: The response enumerates all planned deal fees in the scenario cash model: for example, $2m underwriting fees.
提示: Missing fees and transaction costs leads to over optimistic cash flow forecasts.
出处: prbench:ba626d238986994ead41cc11 | 话题: Corporate Finance

## FIN-0997 [必须]
判据: The response reports the numerical headroom to the 3.5× covenant limit.
提示: Quantifying headroom provides immediate insight into covenant safety margins.
出处: prbench:ba6d07de4bd75056545eb158 | 话题: Accounting & Financial Statement Analysis

## FIN-0998 [必须]
判据: The response defines EBITDA as EBIT plus depreciation plus amortization and recognizes that non-cash items such as impairment charges are excluded from EBITDA.
提示: A correct definition is required for accurate covenant and performance analysis.
出处: prbench:ba6d07de4bd75056545eb158 | 话题: Accounting & Financial Statement Analysis

## FIN-0999 [必须]
判据: The response explains that a change in useful life is treated prospectively under FRS 102.
提示: Clarifying the prospective nature ensures accurate treatment of accounting estimates.
出处: prbench:ba6d07de4bd75056545eb158 | 话题: Accounting & Financial Statement Analysis

## FIN-1000 [必须]
判据: The response states a pre-tax discount rate (e.g., a 7% post-tax rate with a 25% tax rate would be approximately 9.33% pre-tax).
提示: A stated rate allows verification and aligns the VIU computation with accounting standards.
出处: prbench:ba6d07de4bd75056545eb158 | 话题: Accounting & Financial Statement Analysis

## FIN-1001 [必须]
判据: The response calculates deferred-tax movement using the formula: ΔDT = change in temporary difference × 25%.
提示: Deferred tax affects net income and balance sheet accuracy; calculation ensures transparency.
出处: prbench:ba6d07de4bd75056545eb158 | 话题: Accounting & Financial Statement Analysis

## FIN-1002 [必须]
判据: The response defines recoverable amount as the higher of value-in-use (discounted future cash flows) or fair value less costs to sell.
提示: A precise definition ensures correct identification of an impairment trigger.
出处: prbench:ba6d07de4bd75056545eb158 | 话题: Accounting & Financial Statement Analysis

## FIN-1003 [必须]
判据: The response computes the covenant ratio as net debt divided by EBITDA.
提示: This ratio is fundamental to determining lender compliance under loan agreements.
出处: prbench:ba6d07de4bd75056545eb158 | 话题: Accounting & Financial Statement Analysis

## FIN-1004 [必须]
判据: The response defines fair value less costs to sell as market value minus disposal costs.
提示: Including a numeric illustration makes the fair value calculation independently testable.
出处: prbench:ba6d07de4bd75056545eb158 | 话题: Accounting & Financial Statement Analysis

## FIN-1005 [必须]
判据: The response explicitly states that the discount rate used in the earnout valuation must reflect the risk inherent in the contingent payment itself (not the acquirer's WACC or cost of debt), typically reflecting a risk-adjusted rate commensurate with the uncertainty of achieving the milestones.
提示: The user's concern about "too conservative" probabilities directly relates to how risk is captured in the model. Proper discount rate selection is fundamental to supporting or challenging the valuation and is frequently misunderstood.
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1006 [必须]
判据: The response clarifies that "new information about facts and circumstances that existed at the acquisition date" specifically means facts that existed but were unknown at closing (such as undisclosed customer churn or signed contracts not yet in the data room).
提示: This distinction is critical to properly applying the measurement period exception and directly addresses the user's confusion about when goodwill adjustments are appropriate.
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1007 [必须]
判据: The response notes that the fair value measurement must incorporate the company's own credit risk (nonperformance risk) per ASC 820-10-35-18, meaning if the acquirer's creditworthiness deteriorates, the earnout liability's fair value decreases, creating a counterintuitive gain in P&L.
提示: This is a sophisticated and counterintuitive requirement under fair value accounting that experts should understand. Critical for accurate fair value measurement.
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1008 [必须]
判据: The response clarifies that remeasurement frequency (quarterly vs. annually) is a policy election.
提示: Addresses the ambiguity around "quarterly adjustments" mentioned in the prompt
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1009 [必须]
判据: The response explains that a third-party valuation establishes the fair value of the acquisition at the acquisition date.
提示: Important context regarding when and how fair valuation takes place.
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1010 [必须]
判据: The response correctly states that under ASC 805, earnout remeasurement adjustments after the measurement period (typically one year from the acquisition date) are recognized in earnings (P&L), not as adjustments to goodwill.
提示: This is the core technical accounting treatment under current GAAP.
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1011 [必须]
判据: The response explains that the accounting treatment changed from FAS 141 (original) to FAS 141(R)/ASC 805, where the former allowed goodwill adjustments for earnout changes but current guidance requires P&L treatment post-measurement period.
提示: Resolves the confusion expressed in the prompt about conflicting guidance by providing historical context for why the "old auditor" may have used different treatment.
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1012 [负面]
判据: The response incorrectly states that earnout remeasurement adjustments after the measurement period should be recorded as adjustments to goodwill.
提示: This is fundamentally wrong under ASC 805 and would lead to material misstatement. Post-measurement period adjustments must go through P&L.
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1013 [必须]
判据: The response explains that the fair value at the acquisition date can be challenged with substantive contradictory evidence before closing.
提示: This directly answers one of the user's key questions.
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1014 [必须]
判据: The response distinguishes between the measurement period (up to one year post-acquisition, during which new information about facts and circumstances existing at the acquisition date can adjust goodwill) and subsequent remeasurement (which goes to P&L).
提示: Essential technical distinction that explains the confusion in the prompt. The "old auditor" was likely correct if adjustments occurred within the measurement period, but wrong if after.
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1015 [负面]
判据: The response recommends recording earnout adjustments through Retained Earnings as a prior period adjustment rather than through the current period P&L.
提示: Incorrect treatment. Earnout remeasurement is a current period change in estimate, not a correction of error, and should flow through current P&L.
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1016 [必须]
判据: The response explains that the fair value at the acquisition date cannot be overridden based on management judgment.
提示: This answers the user's prompt on pushing back on numbers.
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1017 [必须]
判据: The response clarifies that valuation remeasurement timing does not impact its treatment on the P&L.
提示: Directly answers a question in the prompt.
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1018 [负面]
判据: The response incorrectly claims that management can unilaterally override or ignore the third-party fair value assessment at acquisition based solely on their belief that probabilities are 'too conservative'.
提示: This would constitute a material weakness in financial reporting controls and likely result in audit qualification. Fair value requires objective determination.
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1019 [必须]
判据: The response notes that fair value measurement for the earnout should reflect market participant assumptions, not management's specific knowledge, though entity-specific synergies expected by market participants can be included.
提示: Important technical nuance about fair value that tempers the user's instinct to incorporate their inside knowledge.
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1020 [必须]
判据: The response clarifies that remeasurement is triggered when milestones are achieved (or become probable of being achieved), regardless of timing, meaning early achievement of the year 2 target would require immediate remeasurement at that point.
提示: Directly answers the third explicit question in the prompt about what happens if they "hit milestones earlier than expected."
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1021 [负面]
判据: The response states that early milestone achievement does not require remeasurement of the earnout liability until the original anticipated measurement dates.
提示: Wrong accounting treatment. Achievement of contingent consideration milestones triggers immediate remeasurement obligation.
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1022 [必须]
判据: The response explains that changes in the earnout's fair value must be decomposed into two components: (1) accretion expense from unwinding the discount over time, and (2) changes due to revised assumptions about achievement probabilities or amounts.
提示: This technical decomposition is required for proper financial statement presentation and is frequently missed. The prompt's focus on "quarterly adjustments" should trigger discussion of how the passage of time affects the liability value separately from performance updates.
出处: prbench:ba7635238180eaadc380e2b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1023 [建议]
判据: The response identifies that the £18M annual benefit outflows exceed the current portfolio's yield of 1.8%, requiring asset sales to fund the deficit.
提示: Negative carry quantification highlights yield inadequacy.
出处: prbench:bb2031673ae803da68e16a52 | 话题: Investment Strategy & Portfolio Design

## FIN-1024 [必须]
判据: The response calculates the net funding ratio impact from a +100 bps rate rise, showing the percentage point change (e.g., improving from 87% to ~97%).
提示: The upside scenario quantifies the benefit of a rate rise.
出处: prbench:bb2031673ae803da68e16a52 | 话题: Investment Strategy & Portfolio Design

## FIN-1025 [必须]
判据: The response quantifies the potential equity drawdown's impact on the funding ratio (e.g., a 20% equity loss equals a 7-8 percentage point decline).
提示: Equity risk quantification validates the de-risking rationale.
出处: prbench:bb2031673ae803da68e16a52 | 话题: Investment Strategy & Portfolio Design

## FIN-1026 [必须]
判据: The response calculates the net funding ratio impact from a -100 bps rate fall, showing the percentage point change (e.g., deteriorating from 87% to ~80%).
提示: The downside scenario quantifies the risk of a rate fall.
出处: prbench:bb2031673ae803da68e16a52 | 话题: Investment Strategy & Portfolio Design

## FIN-1027 [必须]
判据: The response quantifies the expected haircut on the £36M property portfolio in a buyout scenario (e.g., insurers applying a 15-25% reduction).
提示: Property valuation risk directly affects buyout pricing.
出处: prbench:bb2031673ae803da68e16a52 | 话题: Investment Strategy & Portfolio Design

## FIN-1028 [必须]
判据: The response calculates the asset's value change from a 100 bps rate movement using the 9-year asset duration (e.g., ~£40.5M movement).
提示: Asset sensitivity quantification is essential for risk assessment.
出处: prbench:bb2031673ae803da68e16a52 | 话题: Investment Strategy & Portfolio Design

## FIN-1029 [必须]
判据: The response quantifies the notional principal of interest rate swaps required to close the duration gap (e.g., £180-250M notional).
提示: Swap sizing is critical for the duration matching solution.
出处: prbench:bb2031673ae803da68e16a52 | 话题: Investment Strategy & Portfolio Design

## FIN-1030 [必须]
判据: The response calculates the liability's value change from a 100 bps rate movement using the 18-year duration (e.g., ~£93M movement).
提示: Interest rate sensitivity drives the scheme's funding volatility.
出处: prbench:bb2031673ae803da68e16a52 | 话题: Investment Strategy & Portfolio Design

## FIN-1031 [必须]
判据: The response assesses economic rationale (expected ROI) for rare-disease acquisitions (e.g., orphan exclusivity, durable pricing, RNAi platform scalability).
提示: Distinguishes capital-efficient diversification from vague portfolio broadening.
出处: prbench:bbde884de8a0263c7016ef3e | 话题: Corporate Finance

## FIN-1032 [必须]
判据: The response assesses the economic rationale (expected ROI) for MASH-related acquisitions (e.g., fibrosis benefit -> payer access -> pricing power -> IRR uplift).
提示: Analysts must link mechanism to return generation; adjacency without ROI logic fails.
出处: prbench:bbde884de8a0263c7016ef3e | 话题: Corporate Finance

## FIN-1033 [必须]
判据: The response assesses economic rationale (expected ROI) for cardiovascular acquisitions (e.g., SELECT outcomes -> reimbursement leverage -> durable volume growth).
提示: Value in CV deals stems from payer economics; omitting that chain weakens credibility.
出处: prbench:bbde884de8a0263c7016ef3e | 话题: Corporate Finance

## FIN-1034 [必须]
判据: The response calculates the exact 3-month EUR/USD forward rate using interest rate parity, showing the formula F = S × (1 + r_USD × T) / (1 + r_EUR × T) with specific interest rates for both currencies.
提示: Tests precise knowledge of forward pricing mechanics
出处: prbench:bceeb814d6e6634cfa395972 | 话题: International Finance & FX Hedging

## FIN-1035 [必须]
判据: The response compares the cost-effectiveness using risk-adjusted return metrics, calculating the Sharpe ratio for both hedging strategies and recommending based on the superior risk-adjusted performance.
提示: Tests advanced portfolio optimisation concepts.
出处: prbench:bceeb814d6e6634cfa395972 | 话题: International Finance & FX Hedging

## FIN-1036 [必须]
判据: The response calculates the capital impact under Basel III rules, showing the specific risk-weighted asset calculation for the derivative exposure and the resulting impact on the company's capital ratios.
提示: Tests advanced regulatory capital knowledge.
出处: prbench:bceeb814d6e6634cfa395972 | 话题: International Finance & FX Hedging

## FIN-1037 [必须]
判据: The response calculates the exact USD proceeds from the forward hedge as €300,000 × the calculated forward rate, showing the specific dollar amount the company will receive.
提示: Tests ability to apply forward pricing to the specific scenario.
出处: prbench:bceeb814d6e6634cfa395972 | 话题: International Finance & FX Hedging

## FIN-1038 [必须]
判据: The response identifies the specific journal entries for both the derivative instrument and the OCI adjustments, showing debits and credits for both the initial recognition and subsequent fair value adjustments.
提示: Tests detailed accounting implementation knowledge.
出处: prbench:bceeb814d6e6634cfa395972 | 话题: International Finance & FX Hedging

## FIN-1039 [必须]
判据: The response notes that no market abuse occurred according to the regulator.
提示: Confirms understanding of the regulator’s finding.
出处: prbench:bd7e6a67fb50dd154e245585 | 话题: Regulation, Compliance & Ethics

## FIN-1040 [必须]
判据: The response states that the fine amount imposed was £2.5 million.
提示: Tests recognition of the factual penalty.
出处: prbench:bd7e6a67fb50dd154e245585 | 话题: Regulation, Compliance & Ethics

## FIN-1041 [必须]
判据: The response states that the cause of the fine was failure to record trader voice calls.
提示: Tests recognition of the factual breach.
出处: prbench:bd7e6a67fb50dd154e245585 | 话题: Regulation, Compliance & Ethics

## FIN-1042 [必须]
判据: The response correctly calculated after-tax profits in Ireland pre-Pillar Two as (60-18-9-7.2)*(1-12.5%)=22.575M.
提示: It should correctly calculate the profits after tax to evaluate and recommend the actions. It is easy to forget subtracting 7.2M that is paid to the US parent.
出处: prbench:bdd08680e6ee24b1e37835cf | 话题: Taxation & Cross-Border Structuring

## FIN-1043 [必须]
判据: The response calculated after-tax profits in Ireland post-Pillar Two under an increased royalty rate of, for example, 20%, as (60-18-9-12)*(1-15%)=17.85M.
提示: When not given a specific range, checking if the profit changes under a different royalty rate is crucial for recommending actions.
出处: prbench:bdd08680e6ee24b1e37835cf | 话题: Taxation & Cross-Border Structuring

## FIN-1044 [必须]
判据: The responses compared different scenarios based on global ETR, which is defined as total tax/total group profit before tax.
提示: It should notice that it's not the profit that they are comparing; rather, it should be comparing the global ETR.
出处: prbench:bdd08680e6ee24b1e37835cf | 话题: Taxation & Cross-Border Structuring

## FIN-1045 [必须]
判据: The response correctly calculated after-tax profits in Ireland post-Pillar Two (meaning a 15% minimum tax) under the current royalty rate of 12% as (60-18-9-7.2)*(1-15%)=21.93M.
提示: It should calculate post-Pillar Two profit under the current royalty to analyze ETR.
出处: prbench:bdd08680e6ee24b1e37835cf | 话题: Taxation & Cross-Border Structuring

## FIN-1046 [必须]
判据: The response explains impermanent loss correctly with a simple example (e.g., if ETH rises relative to USDC, you end up with less ETH than holding).
提示: Checks the response clearly defines IL.
出处: prbench:c001e37b7ca9ce6e2161826f | 话题: FinTech, Crypto & Digital Assets

## FIN-1047 [必须]
判据: Refers to interest/royalty WHT (26%/30% Italy).
提示: Ensures completeness on all cash flow types, not only dividends.
出处: prbench:c24f1c14347b88b604a65c53 | 话题: Taxation & Cross-Border Structuring

## FIN-1048 [必须]
判据: The response includes an explanation on how repo rates affect the present value calculation of the structure.
提示: Repo/financing rates impact the discounting and hedging costs over the 3-year tenor.
出处: prbench:c3d06f45142b644b3c381857 | 话题: Derivatives & Structured Products

## FIN-1049 [必须]
判据: The response mentions the barrier interaction effect: having two barriers at 60% and 65% creates path-dependency that affects joint probability calculations.
提示: Barrier interaction is a key technical consideration in dual-barrier options.
出处: prbench:c3d06f45142b644b3c381857 | 话题: Derivatives & Structured Products

## FIN-1050 [必须]
判据: The response notes that the "memory" feature on the 12% coupon (unpaid coupons accumulate if autocall doesn't trigger) increases the overall structure value.
提示: Memory feature is part of the structure mechanics.
出处: prbench:c3d06f45142b644b3c381857 | 话题: Derivatives & Structured Products

## FIN-1051 [必须]
判据: The response explains that pricing requires multivariate modeling (e.g., Monte Carlo with correlated Brownian motions or copula-based methods) because this is a worst-of structure on 5 names.
提示: Correct modeling framework is fundamental to derivatives pricing.
出处: prbench:c3d06f45142b644b3c381857 | 话题: Derivatives & Structured Products

## FIN-1052 [负面]
判据: The response states that the down-in put/autocallable barrier at 65% can be priced separately without adjustment.
提示: Ignores path dependency and joint probability calculations.
出处: prbench:c3d06f45142b644b3c381857 | 话题: Derivatives & Structured Products

## FIN-1053 [必须]
判据: The response identifies that the correlation between the 5 tech names significantly affects the autocallable valuation.
提示: Correlation impacts the worst-of autocall probability, which affects overall structure value.
出处: prbench:c3d06f45142b644b3c381857 | 话题: Derivatives & Structured Products

## FIN-1054 [必须]
判据: The response identifies that the correlation between the 5 tech names is a primary driver of the down-and-in put cost.
提示: This directly addresses the user's concern about what drives the put pricing and is central to understanding why the intuition of "cheap OTM" fails.
出处: prbench:c3d06f45142b644b3c381857 | 话题: Derivatives & Structured Products

## FIN-1055 [负面]
判据: The response claims correlation doesn't significantly affect the down-and-in put pricing.
提示: Correlation is the primary risk factor in worst-of tail events.
出处: prbench:c3d06f45142b644b3c381857 | 话题: Derivatives & Structured Products

## FIN-1056 [负面]
判据: The response uses the single-name Black-Scholes formula without accounting for the correlation between the 5 names.
提示: Fundamentally wrong approach for worst-of structures.
出处: prbench:c3d06f45142b644b3c381857 | 话题: Derivatives & Structured Products

## FIN-1057 [建议]
判据: The response discusses how funding costs affect the structure valuation over 3 years.
提示: Issuer funding spreads are part of the all-in cost calculation.
出处: prbench:c3d06f45142b644b3c381857 | 话题: Derivatives & Structured Products

## FIN-1058 [必须]
判据: The response recommends a valid advanced statistical method to improve model assumptions (e.g., GARCH, copulas, correlation shrinkage).
提示: Tests knowledge of advanced modelling techniques.
出处: prbench:c56561187840234c4b0b43cf | 话题: Risk Management & Stress Testing

## FIN-1059 [负面]
判据: The response advises using simple volatility scaling for tail events.
提示: Penalises simplistic, dangerous advice for tail events.
出处: prbench:c56561187840234c4b0b43cf | 话题: Risk Management & Stress Testing

## FIN-1060 [必须]
判据: The response identifies that VaR models fail due to fat-tailed distributions.
提示: Tests diagnosis of core statistical problem.
出处: prbench:c56561187840234c4b0b43cf | 话题: Risk Management & Stress Testing

## FIN-1061 [建议]
判据: The response explains that some countries (e.g., Ireland/Luxembourg UCITS funds) receive 15% treaty withholding instead of 30%.
提示: Captures fund-level savings correctly.
出处: prbench:c6b42c67398e6f807344909c | 话题: Taxation & Cross-Border Structuring

## FIN-1062 [必须]
判据: The response states that there are two tax layers: U.S.→fund, fund→investor/home country.
提示: Ensures complete picture of taxation.
出处: prbench:c6b42c67398e6f807344909c | 话题: Taxation & Cross-Border Structuring

## FIN-1063 [必须]
判据: The response describes the payoff if oil remains high: the option expires worthless and only the premium is lost.
提示: Clarifies trade-offs; without it the response leans one-sided but still mostly correct.
出处: prbench:c6ea4243d96eec873c51f692 | 话题: Derivatives & Structured Products

## FIN-1064 [负面]
判据: The response explicitly claims that the hedge provides protection at no cost or is “free.”
提示: Creates a misleading impression that distorts the economics of hedging.
出处: prbench:c6ea4243d96eec873c51f692 | 话题: Derivatives & Structured Products

## FIN-1065 [必须]
判据: The response specifies the correct product as a put option on oil.
提示: Correctly identifying the instrument is the crux of the prompt; misidentification changes the answer entirely.
出处: prbench:c6ea4243d96eec873c51f692 | 话题: Derivatives & Structured Products

## FIN-1066 [必须]
判据: The response explains the payoff mechanism: if oil falls below the strike, the put increases in value, offsetting client losses.
提示: Core explanation of how the product helps; without this, the response is incomplete.
出处: prbench:c6ea4243d96eec873c51f692 | 话题: Derivatives & Structured Products

## FIN-1067 [必须]
判据: The response states that the counterparty (e.g., the bank) is the option seller who provides the hedge.
提示: Counterparty role gives full context, but omission is not fatal.
出处: prbench:c6ea4243d96eec873c51f692 | 话题: Derivatives & Structured Products

## FIN-1068 [负面]
判据: The response suggests buying a call option instead of a put.
提示: This is the most common wrong hedge recommendation; it completely inverts the correct answer.
出处: prbench:c6ea4243d96eec873c51f692 | 话题: Derivatives & Structured Products

## FIN-1069 [必须]
判据: The response states that the option protection only lasts for a defined maturity period (e.g., 6 months).
提示: Duration is a key limit of the hedge, but omitting it does not fully break the answer.
出处: prbench:c6ea4243d96eec873c51f692 | 话题: Derivatives & Structured Products

## FIN-1070 [必须]
判据: The response identifies the client’s risk exposure: the client is naturally short oil, so falling oil prices reduce revenue.
提示: Establishing the exposure is necessary for context but not make-or-break. Important for clarity, not critical.
出处: prbench:c6ea4243d96eec873c51f692 | 话题: Derivatives & Structured Products

## FIN-1071 [必须]
判据: The response identifies the hedging instrument as a derivative contract.
提示: Without naming it as a derivative hedge, the response misses the core of the question.
出处: prbench:c6ea4243d96eec873c51f692 | 话题: Derivatives & Structured Products

## FIN-1072 [必须]
判据: The response quantifies the P&L impact of the 5-year EUR interest rate swap, assuming a flight-to-quality rally (e.g., a 10 bp rate decrease).
提示: Account for all portfolio hedging instruments.
出处: prbench:c6eeed6a5c38902943f146b7 | 话题: Risk Management & Stress Testing

## FIN-1073 [必须]
判据: The response calculates a required hedge notional of approximately £375 million by dividing the Italian sleeve's credit DV01 (~£168,750/bp) by the iTraxx 5Y DV01 (~£450/bp per £1m notional).
提示: A proposed trade is unactionable without precise sizing.
出处: prbench:c6eeed6a5c38902943f146b7 | 话题: Risk Management & Stress Testing

## FIN-1074 [必须]
判据: The response converts the 1-year VaR to a 1-day VaR by dividing the £12 million figure by the square root of 252, resulting in approximately £756,000.
提示: Risk analysis must convert annual to daily VaR.
出处: prbench:c6eeed6a5c38902943f146b7 | 话题: Risk Management & Stress Testing

## FIN-1075 [必须]
判据: The response calculates the mark-to-market loss on the Italian corporate bond holdings as £25.31 million.
提示: The primary loss driver; the first step in crisis analysis.
出处: prbench:c6eeed6a5c38902943f146b7 | 话题: Risk Management & Stress Testing

## FIN-1076 [必须]
判据: The response calculates the final percentage impact on the £1.5bn NAV based on the total net P&L.
提示: The ultimate measure of the crisis's impact on the fund.
出处: prbench:c6eeed6a5c38902943f146b7 | 话题: Risk Management & Stress Testing

## FIN-1077 [必须]
判据: The response calculates the total net P&L by summing the impacts from the Italian bonds, the CDS hedge, and the interest rate swap.
提示: Integrates all P&L sources, not just isolated parts.
出处: prbench:c6eeed6a5c38902943f146b7 | 话题: Risk Management & Stress Testing

## FIN-1078 [必须]
判据: The response calculates the CDS P&L as approximately -£960,000 by multiplying a quantified CS01 of ~£24,000 per basis point by the 40 bps spread move.
提示: Industry standard methodology for pricing credit derivative sensitivity.
出处: prbench:c6eeed6a5c38902943f146b7 | 话题: Risk Management & Stress Testing

## FIN-1079 [必须]
判据: The response identifies that a 40 bps tightening in the iTraxx Europe index results in a mark-to-market loss on the long protection position.
提示: Tests the core principle of credit derivative profit/loss mechanics.
出处: prbench:c6eeed6a5c38902943f146b7 | 话题: Risk Management & Stress Testing

## FIN-1080 [必须]
判据: The response should state that Vega risk is not a factor for 0DTE option pricing.
提示: Vega risk is not a factor for the management of 0DTE risk.
出处: prbench:c7d44b5c3b186138f2506414 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1081 [必须]
判据: The response should state that term options are sensitive to Vega risk as a major factor, but not the only concern (e.g., delta, gamma, theta).
提示: Want to avoid an exclusive focus on VEGA for long term options.
出处: prbench:c7d44b5c3b186138f2506414 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1082 [必须]
判据: The response should state that 0DTE options are not sensitive to interest rate risk. E.g., RHO is not a factor in valuing a 0DTE option.
提示: Rho is not a factor for 0DTE options
出处: prbench:c7d44b5c3b186138f2506414 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1083 [必须]
判据: The response should state that market makers are typically short 0DTE options.
提示: Necessary to understand the structure of the market makers trading book.
出处: prbench:c7d44b5c3b186138f2506414 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1084 [必须]
判据: The response should discuss the impact of time on the value of an option position. E.g., compare time to expiration for 0DTE options and standard one-month stock options.
提示: Time to expiration directly implicates the partial derivative theta which is what the market maker stands to use to oofset heding costs.
出处: prbench:c7d44b5c3b186138f2506414 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1085 [必须]
判据: The response should state that for longer-term options, all main Greeks (Delta, Gamma, Theta, Vega, Rho) are relevant factors in valuation.
提示: This criterion ensures the response identifies the broader risk profile of longer-term options. While not as critical as recognizing which Greeks dominate in 0DTE, it is important for accuracy and completeness.
出处: prbench:c7d44b5c3b186138f2506414 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1086 [必须]
判据: The response should state that Vega risk is a primary factor for options with longer maturities (unlike 0DTE).
提示: Important not but for 0DTE options, just for the comparison for term options.
出处: prbench:c7d44b5c3b186138f2506414 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1087 [必须]
判据: The response should state that the 0DTE market is dominated by retail traders.
提示: GIves a feel for the market structure
出处: prbench:c7d44b5c3b186138f2506414 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1088 [建议]
判据: The response should state that for longer-term options, the Greeks evolve more gradually over time compared to 0DTE.
提示: This adds nuance to how Greeks behave across maturities. It is less central than simply naming the relevant Greeks but still improves the technical precision of the response.
出处: prbench:c7d44b5c3b186138f2506414 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1089 [必须]
判据: The response identifies accounts receivable as a key account to analyse for channel stuffing.
提示: This tests for practical knowledge of how to spot the signs of channel stuffing on the financial statements.
出处: prbench:c837f248c63ec90f904679b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1090 [必须]
判据: The response identifies the improper capitalisation of operating expenses as a likely technique for inflating profits.
提示: This is a core forensic accounting check for understanding the true profitability and cash generation of a business.
出处: prbench:c837f248c63ec90f904679b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1091 [必须]
判据: The response identifies that cash outflows for capitalised costs are found in the investing activities section of the cash flow statement.
提示: This shows a practical understanding of how capitalised expenses are presented across the different financial statements.
出处: prbench:c837f248c63ec90f904679b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1092 [必须]
判据: The response identifies aggressive revenue recognition as a likely technique for inflating profits.
提示: This is one of the most common and significant red flags in the financial analysis of a SaaS company.
出处: prbench:c837f248c63ec90f904679b6 | 话题: Accounting & Financial Statement Analysis

## FIN-1093 [必须]
判据: The response identifies the arrival-price benchmark as the 10:00 NBBO midpoint ($24.99).
提示: Establishes the reference price needed to measure implementation shortfall.
出处: prbench:c89abf106dae22c31a698461 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1094 [必须]
判据: The response provides an IS calculation using the given impact coefficients (0.7 bps temporary, 0.3 bps permanent per 1% ADV).
提示: Verifies numerate understanding and ties choices to costs.
出处: prbench:c89abf106dae22c31a698461 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1095 [必须]
判据: The response explicitly uses the arrival benchmark as the performance measurement baseline.
提示: Split from original 1.
出处: prbench:c89abf106dae22c31a698461 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1096 [必须]
判据: The response correctly calculates the order size as 6% of ADV (1.2M shares ÷ 20M ADV = 6%).
提示: %ADV underpins impact modeling and participation controls.
出处: prbench:c89abf106dae22c31a698461 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1097 [必须]
判据: States explicitly that excluding Investments from overhead allocation inflates its reported EBIT.
提示: Establishes recognition of the key distortion in reported results.
出处: prbench:ca946cf83ee263164da9597e | 话题: Accounting & Financial Statement Analysis

## FIN-1098 [必须]
判据: The response separates recurring investment income (interest/dividends/fees) from fair-value or realized gains/losses.
提示: Improves comparability of volatile vs. stable earnings.
出处: prbench:ca946cf83ee263164da9597e | 话题: Accounting & Financial Statement Analysis

## FIN-1099 [必须]
判据: The response explicitly states that Services EBIT is understated because it bears corporate overhead.
提示: Ensures Services distortion is recognized, not overlooked.
出处: prbench:ca946cf83ee263164da9597e | 话题: Accounting & Financial Statement Analysis

## FIN-1100 [必须]
判据: The response explicitly states that Manufacturing EBIT is understated because it bears corporate overhead.
提示: Ensures the answer identifies the direct impact on Manufacturing.
出处: prbench:ca946cf83ee263164da9597e | 话题: Accounting & Financial Statement Analysis

## FIN-1101 [必须]
判据: The response states that the valuation policy of the firm will now be governed by the principles of Fair Value Measurement under ASC 820 applied quarterly.
提示: quarterly valuations
出处: prbench:cbc8ea215de964366819a192 | 话题: Accounting & Financial Statement Analysis

## FIN-1102 [必须]
判据: The response states that Sarbanes-Oxley requires an internal control audit.
提示: SARBOX 404
出处: prbench:cbc8ea215de964366819a192 | 话题: Accounting & Financial Statement Analysis

## FIN-1103 [必须]
判据: The response states that reporting is governed by lender requirements.
提示: Important to keep accuracy.
出处: prbench:cbc8ea215de964366819a192 | 话题: Accounting & Financial Statement Analysis

## FIN-1104 [必须]
判据: The response states that gamma neutrality protects against large price changes in the underlying asset (e.g., stability of delta, insulation from volatility shocks).
提示: borader options
出处: prbench:ceedcb3f821e768084306dee | 话题: Derivatives & Structured Products

## FIN-1105 [必须]
判据: The response calculates the volatility increase as 1% (from 20% to 21%).
提示: part of user ask
出处: prbench:ceedcb3f821e768084306dee | 话题: Derivatives & Structured Products

## FIN-1106 [必须]
判据: The response calculates Vega to be 0.121 (i.e., using the formula 0.01 x 12.1= 0.121).
提示: main user ask
出处: prbench:ceedcb3f821e768084306dee | 话题: Derivatives & Structured Products

## FIN-1107 [必须]
判据: The response offers the right FX hedges to protect against a stronger USD by naming at least one of the following: Deliverable FX forward; non-deliverable forward (NDF); buy USD call; sell LC (LC put); FX collar (buy USD call + sell USD put).
提示: Checks if the response pick suitable FX tools in the right direction.
出处: prbench:cf68d44643b7154cc283150b | 话题: International Finance & FX Hedging

## FIN-1108 [必须]
判据: The response explicitly states that fuel hedge + FX forward = fixed local currency fuel cost.
提示: checks if the response show two leg hedging stabilize fuel cost.
出处: prbench:cf68d44643b7154cc283150b | 话题: International Finance & FX Hedging

## FIN-1109 [必须]
判据: The response clearly states the local fuel cost equals USD fuel price * exchange rate * volume.
提示: checks if the response shows fuel cost depends on both fuel price and FX together.
出处: prbench:cf68d44643b7154cc283150b | 话题: International Finance & FX Hedging

## FIN-1110 [必须]
判据: The response offers the correct fuel price hedges by naming at least one of the following: Jet fuel swaps/futures, gasoil futures, Brent futures, commodity options (caps/collars).
提示: Checks if the response pick suitable commodities tools.
出处: prbench:cf68d44643b7154cc283150b | 话题: International Finance & FX Hedging

## FIN-1111 [建议]
判据: The response states that MiFID III maintains the fundamental tick size structure from MiFID II.
提示: the tick stricture did not significalty changed under MiFID III
出处: prbench:d024363ce88eed20f8b7e1d6 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1112 [必须]
判据: The response states that the FCA's research demonstrates that tick size increases directly impact trading costs through wider spreads.
提示: part of user's ask.
出处: prbench:d024363ce88eed20f8b7e1d6 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1113 [必须]
判据: The response explains the directional impact of MiFID III adjustments on tick-constrained stocks (e.g., extending the tick-size regime to SIs removes sub-tick price improvement and may increase time spent tick-constrained in highly liquid names).
提示: impact of MiFID
出处: prbench:d024363ce88eed20f8b7e1d6 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1114 [必须]
判据: The response states that when spreads are only one tick wide, market makers cannot provide price enhancement.
提示: further clarifications to user's ask.
出处: prbench:d024363ce88eed20f8b7e1d6 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1115 [必须]
判据: The response states that the FCA’s analysis shows that tick size changes lead to behavioral adaptations, with fewer but larger orders following increases in tick size.
提示: consequences
出处: prbench:d024363ce88eed20f8b7e1d6 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1116 [建议]
判据: The response states that investment banks face constrained price competition when stocks are tick-constrained, limiting their ability to offer price improvements to clients.
提示: tick constrain impatcs
出处: prbench:d024363ce88eed20f8b7e1d6 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1117 [建议]
判据: Response states that gas fees for USDC transfers typically range from USD 2-5 during normal market conditions as of 2025.
提示: realistic cost expectations
出处: prbench:d2db6f8df55fb7370ef6c149 | 话题: FinTech, Crypto & Digital Assets

## FIN-1118 [建议]
判据: Response highlights that USDC specifically accounts for approx. 25% of the total stablecoin market as of Q3 2025.
提示: Further data showing the importance of USDC on the market
出处: prbench:d2db6f8df55fb7370ef6c149 | 话题: FinTech, Crypto & Digital Assets

## FIN-1119 [建议]
判据: Response explicitly names the Dencun upgrade of March 2024 as an event that reduced gas fees.
提示: contiuning ETH upgrades
出处: prbench:d2db6f8df55fb7370ef6c149 | 话题: FinTech, Crypto & Digital Assets

## FIN-1120 [必须]
判据: The response identifies that currency depreciation increases the debt servicing burden in local currency terms for corporate borrowers with FX-denominated or FX-linked loans (the 30% of loans mentioned in the prompt), meaning these borrowers must pay more in local currency to service the same foreign-currency debt.
提示: This tests sophisticated reserve management—understanding that committed near-term obligations reduce truly available reserves for intervention. Failing to make this adjustment could lead to recommending intervention that depletes reserves before the critical rollover, potentially causing a sovereign debt crisis. The adjustment distinguishes between nominal and effective reserve adequacy.
出处: prbench:d34d96a4fe7e8c6ed25369c1 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1121 [必须]
判据: The response quantifies how much inflation will increase from the 12% currency depreciation, stating that it will add approximately 3 to 6 percentage points to inflation over 6-12 months, or referencing 25-50% pass-through rates to calculate this impact.
提示: Quantifying pass-through shows technical sophistication and explains why 12% depreciation materially threatens inflation mandate.
出处: prbench:d34d96a4fe7e8c6ed25369c1 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1122 [必须]
判据: The response adjusts reserve adequacy to account for the $8 billion rollover, stating that effective usable reserves are approximately $87 billion, that effective import cover drops to approximately 4 months after reserving for the rollover, or that it explicitly subtracts the rollover from intervention capacity.
提示: Tests whether the response understands committed obligations reduce available reserves—critical for preventing depletion before rollover.
出处: prbench:d34d96a4fe7e8c6ed25369c1 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1123 [必须]
判据: The response explicitly states that FX intervention alone, by itself, or without monetary tightening cannot successfully stabilize the currency, will fail, is ineffective, or cannot address the underlying pressure.
提示: Expectations dynamics are central to modern monetary policy. This technical concept explains why decisive action now prevents worse outcomes later.
出处: prbench:d34d96a4fe7e8c6ed25369c1 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1124 [必须]
判据: The response recommends cutting interest rates, or pausing rate hikes for an extended period beyond 2-3 months, or maintaining the current stance without further tightening as the final policy position, despite inflation at 6.8% having accelerated from 5.9%.
提示: Catastrophically wrong. With accelerating inflation at 6.8% vs 2-4% target, easing or extended pause destroys credibility and guarantees expectations de-anchoring.
出处: prbench:d34d96a4fe7e8c6ed25369c1 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1125 [必须]
判据: The response explicitly identifies that the central bank faces a policy trilemma (impossible trinity or Mundell-Fleming trilemma) where it cannot simultaneously achieve exchange rate stability, independent monetary policy for domestic price stability, and open capital flows.
提示: Foundational conceptual framework. Without this, analysis treats issues as independent rather than interconnected trade-offs.
出处: prbench:d34d96a4fe7e8c6ed25369c1 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1126 [必须]
判据: The response names one valid Pillar Two election the group could adopt in Ireland, such as the GloBE Safe Harbour Election (e.g., Transitional CbCR Safe Harbour).
提示: Evaluates understanding of Pillar Two application via one concrete election only.
出处: prbench:d44e7bd575ebd8a155806165 | 话题: Taxation & Cross-Border Structuring

## FIN-1127 [必须]
判据: The response lists the current number of R&D staff mentioned in the prompt as 12.
提示: Reinforces substance reporting and headcount transparency.
出处: prbench:d44e7bd575ebd8a155806165 | 话题: Taxation & Cross-Border Structuring

## FIN-1128 [必须]
判据: The response's analysis uses the provided funding mix (60% debt / 40% equity) figures to quantify the impact on the financing function, such as calculating the potential interest deduction capacity.
提示: Applying the specific financial parameters given in the prompt to the financing analysis.
出处: prbench:d44e7bd575ebd8a155806165 | 话题: Taxation & Cross-Border Structuring

## FIN-1129 [负面]
判据: The response equates a company's EBITDA growth with its ability to cover dividends (e.g., high EBITDA means greater ability to cover dividends).
提示: Fundamentally wrong.
出处: prbench:d4983986c111ae1aeb6c2926 | 话题: Corporate Finance

## FIN-1130 [必须]
判据: The response separates maintenance vs. growth CapEx (e.g., stating that maintenance CapEx and growth CapEx have different implications; maintenance CapEx involves investing in existing assets, while growth CapEx is about spending on new assets or expanding capacity).
提示: They have different implications.
出处: prbench:d4983986c111ae1aeb6c2926 | 话题: Corporate Finance

## FIN-1131 [必须]
判据: The response quantifies two years of forward cash coverage (e.g., OCF – CapEx – interest – amortization vs dividend target) mathematically.
提示: Central metric for linking profits to cash.
出处: prbench:d4983986c111ae1aeb6c2926 | 话题: Corporate Finance

## FIN-1132 [负面]
判据: The response claims the rapid stock price increases may be a result of improving business performance (e.g., improving margins, new deals, promising partnerships).
提示: This is objectively impossible in this scenario as 1) the prompt explicitly explains that earnings results have not had an impact on the price trend, and 2) any price increases from improving business performance would result in a commensurate increase in market cap.
出处: prbench:d5054aed5e676b8d5740a15b | 话题: Market Microstructure, Trading & Liquidity

## FIN-1133 [必须]
判据: The response suggests that the company increased its public float by leveraging ATM (at-the-market) equity offerings (i.e., selling in the open market at market prices).
提示: In practice, this would not be possible for a stock like this that has demonstrated a substantial negative return over a short time frame. It wouldn't be able to find buyers on the open market and likely would not qualify to begin with due to market cap and liquidity requirements.
出处: prbench:d5054aed5e676b8d5740a15b | 话题: Market Microstructure, Trading & Liquidity

## FIN-1134 [必须]
判据: The response explains that reverse splits increase a stock's price without impacting its market cap (e.g., a 1-for-5 reverse split would increase price by 5x; a 1-for-10 reverse split would increase price by 10x; market cap remains constant).
提示: This explicitly explains the puzzle around how the market cap could consistently and steadily decline while stock price experiences significant volatility. The response must correctly recognize that stock price DOES NOT equal market cap.
出处: prbench:d5054aed5e676b8d5740a15b | 话题: Market Microstructure, Trading & Liquidity

## FIN-1135 [必须]
判据: The response concludes that the company is leveraging a discounted PIPE to increase its public float (i.e., issuing shares at a discount to an external private investor).
提示: This is a critical conclusion and the only possible explanation for how the stock continues to move in a cyclical pattern without getting delisted off the NASDAQ.
出处: prbench:d5054aed5e676b8d5740a15b | 话题: Market Microstructure, Trading & Liquidity

## FIN-1136 [必须]
判据: The response identifies that the private investor involved in the PIPE agreement is profiting from the discount spread by selling newly issued company shares in the open market (i.e., the difference between the discounted share price and the market share price).
提示: This explains why the private investor continues to invest in a clearly declining company over a 4-year period - precisely because there is a guaranteed arbitrage opportunity from receiving discounted shares and then immediately dumping them in the open market.
出处: prbench:d5054aed5e676b8d5740a15b | 话题: Market Microstructure, Trading & Liquidity

## FIN-1137 [必须]
判据: The response calculates mezzanine investors' ownership based on a fixed post-money valuation of €375k/(€4.5 million * (1-0.35))=12.82%.
提示: One of the three common conversion methods
出处: prbench:d5ebb041a6e5d5c75749d865 | 话题: Alternative Investments & Private Markets

## FIN-1138 [必须]
判据: The response states that at a €4.5 million post-money valuation, investors pay around €8.56 per share.
提示: Highest price per share is relevant since there's no down-round protection
出处: prbench:d5ebb041a6e5d5c75749d865 | 话题: Alternative Investments & Private Markets

## FIN-1139 [建议]
判据: The response notes that fixing the post-money valuation at €4.5 million dilutes the founders maximally (around 76% ownership).
提示: Important for investor-founder relationship
出处: prbench:d5ebb041a6e5d5c75749d865 | 话题: Alternative Investments & Private Markets

## FIN-1140 [必须]
判据: The response calculates the share price based on a fixed pre-money valuation of €4 million/400k=€10.
提示: One of the three common conversion methods
出处: prbench:d5ebb041a6e5d5c75749d865 | 话题: Alternative Investments & Private Markets

## FIN-1141 [负面]
判据: The response's recommended conversion method has the highest founder dilution (around 76% ownership).
提示: Puts a strain on the relationship
出处: prbench:d5ebb041a6e5d5c75749d865 | 话题: Alternative Investments & Private Markets

## FIN-1142 [负面]
判据: The response's recommended conversion method has the highest price per share for investors (around €10).
提示: Very low down-round protection
出处: prbench:d5ebb041a6e5d5c75749d865 | 话题: Alternative Investments & Private Markets

## FIN-1143 [必须]
判据: The response analyzes factors that impact whether the 375K in promissory notes convert before or alongside the new investment (e.g., discount structure, seniority of noteholders).
提示: One of the three common conversion methods
出处: prbench:d5ebb041a6e5d5c75749d865 | 话题: Alternative Investments & Private Markets

## FIN-1144 [建议]
判据: The response's most expensive method yields a post-money valuation of approximately €5.076 million.
提示: Overvaluation is to be avoided
出处: prbench:d5ebb041a6e5d5c75749d865 | 话题: Alternative Investments & Private Markets

## FIN-1145 [必须]
判据: The response states that ownership percentage corresponds directly to relative voting power (e.g., proportional voting rights, board election influence).
提示: Interested in mitigating mezzanine investor voting power
出处: prbench:d5ebb041a6e5d5c75749d865 | 话题: Alternative Investments & Private Markets

## FIN-1146 [必须]
判据: The response states that a low share price (i.e., 30%+ discount to post-money share price) protects against the lack of an antidilution clause (e.g., lower dilution sensitivity, downside protection).
提示: Important, since there's no down-round protection
出处: prbench:d5ebb041a6e5d5c75749d865 | 话题: Alternative Investments & Private Markets

## FIN-1147 [建议]
判据: The response states that fixing the pre-money valuation at €4 million leads to investor ownership of around 9.85%.
提示: Inherently interested in maximizing investor ownership
出处: prbench:d5ebb041a6e5d5c75749d865 | 话题: Alternative Investments & Private Markets

## FIN-1148 [必须]
判据: The response states that a 35% discount significantly increases ownership share relative to invested capital.
提示: fundamental understanding of discount.
出处: prbench:d5ebb041a6e5d5c75749d865 | 话题: Alternative Investments & Private Markets

## FIN-1149 [必须]
判据: The response translates cross-asset correlations into a change in regulatory capital metrics (e.g., VaR/ES, CET1).
提示: Needs both correlation mechanics and capital translation
出处: prbench:d7dfd8fb26974bc3f591650f | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1150 [必须]
判据: The response quantifies the translation of a modelled property shock into MTM or regulatory capital effects (e.g., “a 5 % decline in bond prices reduces CET1 by ~0.8 pp” or “a £10 bn MTM loss lowers tangible equity by 3 %”).
提示: quantified balance-sheet impact
出处: prbench:d7dfd8fb26974bc3f591650f | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1151 [必须]
判据: The response explicitly states both of the following: for the USD share class, the outcome is affected by the GBP/USD exchange rate; for the EUR share class, the outcome is affected by the GBP/EUR exchange rate.
提示: checks correct currency translation steps are explained.
出处: prbench:d84082e8670ef63bc3dece91 | 话题: International Finance & FX Hedging

## FIN-1152 [必须]
判据: The response states both management and performance fees are charged in the share class currency (USD or EUR).
提示: Verify the response understands what drives returns and fees (part 2).
出处: prbench:d84082e8670ef63bc3dece91 | 话题: International Finance & FX Hedging

## FIN-1153 [必须]
判据: The response explicitly states the fund's NAV is calculated in GBP.
提示: Verify if the response understands what drives returns and fees (part 1).
出处: prbench:d84082e8670ef63bc3dece91 | 话题: International Finance & FX Hedging

## FIN-1154 [必须]
判据: The response separates optical EPS impact from economic value impact (e.g., showing that EPS dilution ≠ value destruction if the return on invested capital exceeds the Weighted Average Cost of Capital, showing that firm value improves once funding risk is mitigated).
提示: This shows economic understanding, not just accounting.
出处: prbench:d946a55b105b4e8e6507d57d | 话题: Corporate Finance

## FIN-1155 [必须]
判据: The model estimates the quantitative Weighted Average Cost of Capital (WACC) differential between “act now” (10%) and “delay 6 mo @ 7.5%” (10.7–10.9%).
提示: This shows a dynamic understanding of WACC drift over a 6-month horizon.
出处: prbench:d946a55b105b4e8e6507d57d | 话题: Corporate Finance

## FIN-1156 [必须]
判据: The response correctly recognizes that investment-grade names (e.g., large global banks, energy companies) widen 100-150 bps under stress.
提示: Helps quantify severity estimates.
出处: prbench:db2bcfcf59d471f8263786f5 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1157 [必须]
判据: The response mentions that high-yield industrials suffer a greater spread beta by 4-5 times versus investment-grade corporates.
提示: Demonstrates understanding of differential market pricing.
出处: prbench:db2bcfcf59d471f8263786f5 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1158 [必须]
判据: Identifies the software development asset account affected by capitalization decisions (e.g., Capitalized software development costs, Software development in progress).
提示: Confirms correct balance-sheet classification.
出处: prbench:dd745c571fcfbfcdbf686923 | 话题: Accounting & Financial Statement Analysis

## FIN-1159 [建议]
判据: Specifies that bundled consideration is allocated using relative standalone selling prices (SSP).
提示: Anchors allocation in the required principle.
出处: prbench:dd745c571fcfbfcdbf686923 | 话题: Accounting & Financial Statement Analysis

## FIN-1160 [必须]
判据: States that support revenue are recognized over time based on time-elapsed progress.
提示: Confirms proper recognition pattern for services.
出处: prbench:dd745c571fcfbfcdbf686923 | 话题: Accounting & Financial Statement Analysis

## FIN-1161 [必须]
判据: States that a lease liability is recognized for future lease payments.
提示: Verifies full dual recognition.
出处: prbench:dd745c571fcfbfcdbf686923 | 话题: Accounting & Financial Statement Analysis

## FIN-1162 [必须]
判据: States that periodic impairment testing is required for capitalized development costs.
提示: Ensures compliance with subsequent measurement rules.
出处: prbench:dd745c571fcfbfcdbf686923 | 话题: Accounting & Financial Statement Analysis

## FIN-1163 [必须]
判据: Identifies the specific revenue line item affected by changes in bundled contract accounting (e.g., software license revenue, support service revenue).
提示: Ensures clarity on income-statement impact.
出处: prbench:dd745c571fcfbfcdbf686923 | 话题: Accounting & Financial Statement Analysis

## FIN-1164 [必须]
判据: Specifies consistent foreign currency procedures covering functional currency determination using economic indicators (e.g., revenue, expenses, financing, inter-company currency exchange).
提示: foreign currency translation
出处: prbench:dd745c571fcfbfcdbf686923 | 话题: Accounting & Financial Statement Analysis

## FIN-1165 [必须]
判据: States that license revenue is recognized at a point in time when control transfers.
提示: Tests application of ASC 606/IFRS 15 timing.
出处: prbench:dd745c571fcfbfcdbf686923 | 话题: Accounting & Financial Statement Analysis

## FIN-1166 [必须]
判据: States that a right-of-use asset is recognized for operating leases.
提示: Confirms asset recognition under ASC 842/IFRS 16.
出处: prbench:dd745c571fcfbfcdbf686923 | 话题: Accounting & Financial Statement Analysis

## FIN-1167 [建议]
判据: Specifies that recognized compensation cost is amortized over the requisite service period.
提示: Verifies correct expense pattern.
出处: prbench:dd745c571fcfbfcdbf686923 | 话题: Accounting & Financial Statement Analysis

## FIN-1168 [必须]
判据: The response treats the “12% net IRR gross of fees” phrase as a deal-breaking credibility issue, not just a red flag.
提示: Any serious LP analysis has to flag inconsistent return metrics as a trust issue.
出处: prbench:de5a3688be270a23b3b0a615 | 话题: Alternative Investments & Private Markets

## FIN-1169 [必须]
判据: The response evaluates alignment via escrow with numbers.
提示: Must check.
出处: prbench:de5a3688be270a23b3b0a615 | 话题: Alternative Investments & Private Markets

## FIN-1170 [必须]
判据: The response benchmarks returns against core-plus infra norms (8–10% net, 1.5x+ TVPI over 10y).
提示: Context is everything.
出处: prbench:de5a3688be270a23b3b0a615 | 话题: Alternative Investments & Private Markets

## FIN-1171 [必须]
判据: The response quantifies the impact of pref resets on LP compounding over multiple vintages.
提示: Need to compound the losses.
出处: prbench:de5a3688be270a23b3b0a615 | 话题: Alternative Investments & Private Markets

## FIN-1172 [建议]
判据: The response identifies which entity has the financial capacity to bear risks related to IP development.
提示: Verifies economic substance of risk allocation
出处: prbench:deae671b558ed5bd64572045 | 话题: Taxation & Cross-Border Structuring

## FIN-1173 [必须]
判据: The response identifies all five DEMPE functions (Development, Enhancement, Maintenance, Protection, and Exploitation of intellectual property) relevant to IP value creation.
提示: Establishes framework for transfer pricing analysis
出处: prbench:deae671b558ed5bd64572045 | 话题: Taxation & Cross-Border Structuring

## FIN-1174 [必须]
判据: The response states that the development function is specific to the Singapore R&D entity, acknowledging its role in creating the core technology.
提示: Establishes alignment between R&D activities and entity purpose
出处: prbench:deae671b558ed5bd64572045 | 话题: Taxation & Cross-Border Structuring

## FIN-1175 [必须]
判据: The response explains that the Income Inclusion Rule (IIR) applies when the French parent includes its proportionate share of low-taxed income from the Irish subsidiary in its tax base.
提示: Establishes basic IIR application mechanism
出处: prbench:deae671b558ed5bd64572045 | 话题: Taxation & Cross-Border Structuring

## FIN-1176 [必须]
判据: The response calculates top-up tax as (15% - Jurisdictional ETR) × (GloBE Income - SBIE), where SBIE equals 5% of eligible payroll plus 5% of eligible tangible assets.
提示: Ensures proper application of substance-based exclusion
出处: prbench:deae671b558ed5bd64572045 | 话题: Taxation & Cross-Border Structuring

## FIN-1177 [建议]
判据: The response states that the UTPR allocation formula gives equal 50% weighting to both employee headcount and tangible asset factors.
提示: Specifies correct proportional weighting
出处: prbench:deae671b558ed5bd64572045 | 话题: Taxation & Cross-Border Structuring

## FIN-1178 [必须]
判据: The response explains the application sequence: QDMTT first (if implemented by subsidiary jurisdiction), then IIR (applied by ultimate parent), then UTPR (applied by other entities if neither QDMTT nor IIR apply).
提示: Provides proper rule application sequence
出处: prbench:deae671b558ed5bd64572045 | 话题: Taxation & Cross-Border Structuring

## FIN-1179 [必须]
判据: The response includes at least three specific DEMPE functions (Development, Enhancement, and Exploitation) when analyzing arm's length profit allocation between entities.
提示: Ensures comprehensive functional analysis
出处: prbench:deae671b558ed5bd64572045 | 话题: Taxation & Cross-Border Structuring

## FIN-1180 [必须]
判据: The response explains that Irish QDMTT (if implemented) would be credited against any French IIR top-up tax calculation for the Irish subsidiary.
提示: Clarifies primary top-up tax mechanism interaction
出处: prbench:deae671b558ed5bd64572045 | 话题: Taxation & Cross-Border Structuring

## FIN-1181 [必须]
判据: The response states intragroup IP licensing arrangements by distinguishing between legal ownership (entity holding registered IP rights) and economic ownership (entity making key development decisions).
提示: Addresses specific prompt concern about intragroup arrangements
出处: prbench:deae671b558ed5bd64572045 | 话题: Taxation & Cross-Border Structuring

## FIN-1182 [必须]
判据: The response states that the French parent would calculate a top-up tax on Irish income if Ireland's effective tax rate falls below 15%.
提示: Addresses specific application to low-taxed Irish income
出处: prbench:deae671b558ed5bd64572045 | 话题: Taxation & Cross-Border Structuring

## FIN-1183 [建议]
判据: The response mentions that UTPR (Undertaxed Payments Rule) allocation keys between France and Ireland include employee headcount in each country.
提示: Identifies one correct allocation factor
出处: prbench:deae671b558ed5bd64572045 | 话题: Taxation & Cross-Border Structuring

## FIN-1184 [建议]
判据: The response states that qualifying R&D expenditure excludes costs for outsourcing activities to related parties.
提示: Identifies specific exclusion affecting nexus ratio calculation
出处: prbench:deae671b558ed5bd64572045 | 话题: Taxation & Cross-Border Structuring

## FIN-1185 [建议]
判据: The response mentions that UTPR (Undertaxed Payments Rule) allocation keys between France and Ireland include tangible assets located in each country.
提示: Identifies second correct allocation factor
出处: prbench:deae671b558ed5bd64572045 | 话题: Taxation & Cross-Border Structuring

## FIN-1186 [必须]
判据: The response calculates the jurisdictional Pillar Two effective tax rate (ETR) as ETR = Adjusted Covered Taxes / GloBE Income for each entity in France, Ireland, and Singapore.
提示: Establishes correct calculation method for jurisdictional tax exposure
出处: prbench:deae671b558ed5bd64572045 | 话题: Taxation & Cross-Border Structuring

## FIN-1187 [建议]
判据: The response explains how pre-existing IP contributions to cost-sharing arrangements are valued for buy-in payments using either the Income Method (projecting future cash flows from the IP), Market Method (using comparable third-party transactions), or Cost Method (historical development costs plus markup).
提示: Ensures fair valuation of initial contributions
出处: prbench:deae671b558ed5bd64572045 | 话题: Taxation & Cross-Border Structuring

## FIN-1188 [必须]
判据: The response addresses whether Ireland has implemented QDMTT (implemented since January 2024 through the Finance Act 2023).
提示: Acknowledges specific jurisdictional implementation status
出处: prbench:deae671b558ed5bd64572045 | 话题: Taxation & Cross-Border Structuring

## FIN-1189 [必须]
判据: The response does not attribute enforcement fines for confirmation delays to ESMA as the fining authority.
提示: Enforcement for these breaches is led by national competent authorities. This keeps the analysis institutionally accurate.
出处: prbench:e041edf24d630bed688783ec | 话题: Regulation, Compliance & Ethics

## FIN-1190 [必须]
判据: The response states that under EMIR, for credit derivative trades between financial counterparties or NFC+ entities, the confirmation deadline is T+1.
提示: This confirms precise knowledge of the T+1 deadline for credit derivatives under EMIR Delegated Regulation (EU) 149/2013, Article 12. It can be graded by checking for explicit reference to credit trades.
出处: prbench:e041edf24d630bed688783ec | 话题: Regulation, Compliance & Ethics

## FIN-1191 [必须]
判据: The response states that the timely confirmation obligation under EMIR applies to non-cleared over-the-counter derivatives.
提示: Scope matters. This ensures the rule is applied to the correct segment of derivatives activity.
出处: prbench:e041edf24d630bed688783ec | 话题: Regulation, Compliance & Ethics

## FIN-1192 [必须]
判据: The response states that under EMIR risk mitigation RTS, the EU counterparty has the legal duty to confirm over-the-counter derivative trades within required timelines that vary by asset class. For example, for interest rates and credit derivatives, the confirmation deadline is T+1; when an NFC is involved, the timeline is T+2.
提示: This criterion tests whether the responder knows the core legal requirement forming the basis of EMIR compliance. Without this, the reasoning fails to address the prompt’s central issue.
出处: prbench:e041edf24d630bed688783ec | 话题: Regulation, Compliance & Ethics

## FIN-1193 [必须]
判据: The response cites Delegated Regulation 149/2013 Article 12 as the instrument that sets confirmation timelines.
提示: Timelines live in the RTS. Naming Article 12 is a precise accuracy check for the deadline source.
出处: prbench:e041edf24d630bed688783ec | 话题: Regulation, Compliance & Ethics

## FIN-1194 [必须]
判据: The response states that larger tick sizes tend to produce firmer, more stable quotes.
提示: Key benefit that explains when larger ticks help execution.
出处: prbench:e14653c439e8af956e7dcc26 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1195 [必须]
判据: The response states that larger tick sizes tend to increase displayed size at or near the NBBO.
提示: Complements quote firmness - important for understanding execution improvements.
出处: prbench:e14653c439e8af956e7dcc26 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1196 [必须]
判据: The response notes that U.S. NMS stocks ≥$1 generally use $0.01 increments.
提示: Important contextual information for US-based junior PM.
出处: prbench:e14653c439e8af956e7dcc26 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1197 [负面]
判据: The response claims that tighter spreads always increase market liquidity or that larger tick sizes always widen spreads.
提示: Fundamental error that would mislead the junior PM about core microstructure relationships.
出处: prbench:e14653c439e8af956e7dcc26 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1198 [必须]
判据: The response contrasts tick size effects between small-cap and large-cap stocks (e.g., large-caps benefit more from tighter ticks; small-caps may lose displayed depth).
提示: Directly relevant to user's mention of small-cap execution.
出处: prbench:e14653c439e8af956e7dcc26 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1199 [负面]
判据: The response defines tick size as trade size, lot size, or any concept other than minimum price increment.
提示: Basic definitional error that would undermine entire explanation.
出处: prbench:e14653c439e8af956e7dcc26 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1200 [必须]
判据: The response defines tick size as the minimum price increment between quotes/orders in a market.
提示: Fundamental definition essential for understanding everything else.
出处: prbench:e14653c439e8af956e7dcc26 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1201 [负面]
判据: The response asserts that smaller ticks are always better for everyone.
提示: Completely misses the central point of the user's question about conflicting advice.
出处: prbench:e14653c439e8af956e7dcc26 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1202 [必须]
判据: The response states that smaller ticks reduce liquidity providers' per-share profit margins.
提示: Key mechanism explaining why smaller isn't always better.
出处: prbench:e14653c439e8af956e7dcc26 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1203 [必须]
判据: The response explains that smaller tick sizes tend to compress quoted spreads through tighter price competition.
提示: Core relationship between tick size and spreads - central to user's question.
出处: prbench:e14653c439e8af956e7dcc26 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1204 [负面]
判据: The response makes contradictory statements about tick size effects (e.g., claiming both that smaller ticks improve and worsen the same execution metric).
提示: Would create confusion rather than clarity for someone learning the concepts.
出处: prbench:e14653c439e8af956e7dcc26 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1205 [必须]
判据: The response clarifies that as long as shares are not sold by the estate upon the individual's passing, they can be dispersed to beneficiaries without triggering a realisation event.
提示: This explains how estates can defer CGT tax liabilities.
出处: prbench:e160b23ef8a3b586703a2ad7 | 话题: Taxation & Cross-Border Structuring

## FIN-1206 [必须]
判据: The response explains that loss harvesting is the realisation of losses to generate a capital gains tax deduction.
提示: This is required to explain the advice on loss harvesting.
出处: prbench:e160b23ef8a3b586703a2ad7 | 话题: Taxation & Cross-Border Structuring

## FIN-1207 [必须]
判据: The response explains that a wash sale is the selling then repurchasing of an asset purely to realize a capital loss.
提示: This is required to explain what a wash sale is.
出处: prbench:e160b23ef8a3b586703a2ad7 | 话题: Taxation & Cross-Border Structuring

## FIN-1208 [必须]
判据: The response explains that Australia provides a 50% discount on capital gains tax when the stock has been held for over 12 months.
提示: This explains the reason for selling longer held assets.
出处: prbench:e160b23ef8a3b586703a2ad7 | 话题: Taxation & Cross-Border Structuring

## FIN-1209 [负面]
判据: The response treats property costs (e.g., taxes, insurance, interest) during possession delays as static costs (i.e., numbers do not change).
提示: Costs should scale.
出处: prbench:e3a8cc1c2f7611e9b6f72e60 | 话题: Risk Management & Stress Testing

## FIN-1210 [必须]
判据: The response identifies the DEMPE framework as the OECD’s required standard for attributing income from intangible assets to the entities performing those functions.
提示: Linking DEMPE explicitly to OECD rules demonstrates accurate awareness of its regulatory authority and ensures factual compliance in reasoning.
出处: prbench:e488456b551d0e7257dbda65 | 话题: Taxation & Cross-Border Structuring

## FIN-1211 [必须]
判据: The response states that the six percent margin must be arm’s length (e.g., it aligns with returns observed in comparable uncontrolled transactions or benchmarking studies).
提示: This ensures the margin is grounded in objective market evidence, not arbitrary estimation. It verifies factual alignment with OECD arm’s-length standards.
出处: prbench:e488456b551d0e7257dbda65 | 话题: Taxation & Cross-Border Structuring

## FIN-1212 [建议]
判据: The response explains how the chosen operating model determines the Dutch entity’s compensation structure (e.g., cost-plus markup for services or spread for sub-licensing).
提示: Describing compensation alignment verifies comprehension of the link between model selection and arm’s-length pricing.
出处: prbench:e488456b551d0e7257dbda65 | 话题: Taxation & Cross-Border Structuring

## FIN-1213 [建议]
判据: The response explains the transfer pricing method selection for the 6 percent (e.g., most appropriate methods are TNMM for services, CUP/royalty benchmarking, or profit split where both NL and SG contribute to DEMPE).
提示: for the 6%
出处: prbench:e488456b551d0e7257dbda65 | 话题: Taxation & Cross-Border Structuring

## FIN-1214 [必须]
判据: The response states that the six percent margin must be tied to DEMPE functions (e.g., defined as Development, Enhancement, Maintenance, Protection, and Exploitation of intangibles) under OECD transfer-pricing guidance.
提示: This confirms the respondent recognizes that the margin must reflect the entity’s contribution to value-creating DEMPE functions rather than legal ownership alone, satisfying core OECD alignment.
出处: prbench:e488456b551d0e7257dbda65 | 话题: Taxation & Cross-Border Structuring

## FIN-1215 [必须]
判据: The response defines non-refundable tax credits as those that can only offset existing tax liability and cannot generate a tax refund when credits exceed tax due.
提示: Establishes clear understanding of this tax credit category
出处: prbench:e55d60b7d55e147ba64578d5 | 话题: Taxation & Cross-Border Structuring

## FIN-1216 [必须]
判据: The response provides a specific withholding tax rate for at least one type of payment (dividends, interest, or royalties) between a named country and South Korea, such as US-Korea dividends (15% under treaty), Netherlands-Korea interest (10% under treaty), or Germany-Korea royalties (10% under treaty).
提示: Necessary for evaluating repatriation efficiency
出处: prbench:e55d60b7d55e147ba64578d5 | 话题: Taxation & Cross-Border Structuring

## FIN-1217 [建议]
判据: The response states that transferable credits are typically used when the original recipient cannot fully utilize the credits against their own tax liability.
提示: Explains the practical purpose of transferability
出处: prbench:e55d60b7d55e147ba64578d5 | 话题: Taxation & Cross-Border Structuring

## FIN-1218 [建议]
判据: The response defines transferable tax credits as those that can be sold or transferred to other taxpayers.
提示: Establishes basic definition of transferability
出处: prbench:e55d60b7d55e147ba64578d5 | 话题: Taxation & Cross-Border Structuring

## FIN-1219 [必须]
判据: The response states, “Nonrefundable or transferable credits reduce the Pillar Two global minimum tax rate because they are not counted as covered taxes,” or a direct paraphrase. Pillar Two means the OECD 15% minimum tax rules for large multinationals.
提示: Identifies key impact on global minimum tax calculations
出处: prbench:e55d60b7d55e147ba64578d5 | 话题: Taxation & Cross-Border Structuring

## FIN-1220 [建议]
判据: The response explicitly states that, under OECD Pillar Two (GloBE) rules, Qualified Refundable Tax Credits (QRTCs) are treated as income (i.e., included in GloBE income rather than as a reduction of covered taxes) for the effective tax rate calculation.
提示: Critical distinction affecting global minimum tax calculations
出处: prbench:e55d60b7d55e147ba64578d5 | 话题: Taxation & Cross-Border Structuring

## FIN-1221 [必须]
判据: The response defines refundable tax credits as those providing cash payments when credits exceed tax liability.
提示: Establishes clear understanding of a key tax credit type
出处: prbench:e55d60b7d55e147ba64578d5 | 话题: Taxation & Cross-Border Structuring

## FIN-1222 [必须]
判据: The response quantifies the specific cost impact of the 5-cent tick size increase on implementation shortfall, such as calculating the 400% spread widening effect on the 15-20bps degradation.
提示: Quantifying the regulatory impact provides measurable validation of the root cause hypothesis.
出处: prbench:e63c19a2d4182b82a6611ca9 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1223 [必须]
判据: The response must state that unhedged EUR investors gain when USD appreciates against EUR.
提示: Strong USD typically hurts EM equities (capital outflows, higher debt servicing); necessary to capture full impact.
出处: prbench:e6a65e76b7092d4d60483836 | 话题: Investment Strategy & Portfolio Design

## FIN-1224 [必须]
判据: The response must identify at least one channel through which USD strength pressures EM debt (e.g., higher servicing costs for USD-denominated bonds).
提示: A valid strategic recommendation must show actionable reallocation.
出处: prbench:e6a65e76b7092d4d60483836 | 话题: Investment Strategy & Portfolio Design

## FIN-1225 [必须]
判据: The response calculates Expected Positive Exposure (EPE) using the simulated PFE profile, applying the formula: EPE= 1/T∑iPFE(ti)*Δt i or an equivalent discrete-time average.
提示: Critical component of CVA calculation
出处: prbench:e6e3bd0160e421fc7888ed34 | 话题: Risk Management & Stress Testing

## FIN-1226 [必须]
判据: The response correctly applies the given recovery rate (RR) of 30% (yielding a loss given default, LGD, of 70%) in the CVA calculation.
提示: Required for proper loss estimation in the CVA formula
出处: prbench:e6e3bd0160e421fc7888ed34 | 话题: Risk Management & Stress Testing

## FIN-1227 [必须]
判据: The response specifies suitable parameters for the distribution of jump sizes for ETH in the jump-diffusion model, including the mean (acceptable range: mean jump size μJ between -0.3 and +0.2).
提示: Necessary for modeling magnitude of ETH price shocks
出处: prbench:e6e3bd0160e421fc7888ed34 | 话题: Risk Management & Stress Testing

## FIN-1228 [必须]
判据: The response correctly outlines the first step of Monte Carlo simulation for PFE: simulating multiple ETH price paths using Merton's jump-diffusion model with the specified parameters.
提示: Fundamental initial step in the PFE calculation process
出处: prbench:e6e3bd0160e421fc7888ed34 | 话题: Risk Management & Stress Testing

## FIN-1229 [必须]
判据: The response specifies suitable parameters for the distribution of jump sizes for ETH in the jump-diffusion model, including standard deviation (σJ between 0.1 and 0.3).
提示: Necessary for modeling magnitude of ETH price shocks
出处: prbench:e6e3bd0160e421fc7888ed34 | 话题: Risk Management & Stress Testing

## FIN-1230 [必须]
判据: The response specifies an appropriate volatility parameter value for ETH in the jump-diffusion model (acceptable range: approximately 60-120% annualized, e.g., σ=80%).
提示: Critical parameter for accurately modeling ETH price movements
出处: prbench:e6e3bd0160e421fc7888ed34 | 话题: Risk Management & Stress Testing

## FIN-1231 [必须]
判据: The response correctly outlines the second step of Monte Carlo simulation for PFE: calculating the option exposure at each time point along each simulated price path.
提示: Essential intermediate calculation in the PFE methodology
出处: prbench:e6e3bd0160e421fc7888ed34 | 话题: Risk Management & Stress Testing

## FIN-1232 [必须]
判据: The response correctly applies the given probability of default (PD) of 4% per annum in the CVA calculation.
提示: Essential for accurate counterparty risk quantification
出处: prbench:e6e3bd0160e421fc7888ed34 | 话题: Risk Management & Stress Testing

## FIN-1233 [必须]
判据: The response provides the correct formula for CVA (LGD × EPE × PD).
提示: Fundamental formula for counterparty risk quantification
出处: prbench:e6e3bd0160e421fc7888ed34 | 话题: Risk Management & Stress Testing

## FIN-1234 [必须]
判据: The response specifies an appropriate jump intensity parameter for ETH in the jump-diffusion model (acceptable range: approximately 0.1-0.5 jumps per year, e.g., λ=0.2).
提示: Essential for capturing frequency of significant price dislocations
出处: prbench:e6e3bd0160e421fc7888ed34 | 话题: Risk Management & Stress Testing

## FIN-1235 [必须]
判据: The response appropriately models the non-linear payoff structure of the European call option on ETH in the exposure calculations.
提示: Essential for accurate option exposure modeling
出处: prbench:e6e3bd0160e421fc7888ed34 | 话题: Risk Management & Stress Testing

## FIN-1236 [必须]
判据: The response correctly outlines the third step of Monte Carlo simulation for PFE: computing the 95th percentile of exposure values at each date across all paths to derive the PFE profile over the option's lifetime.
提示: Critical final step in generating the required PFE profile
出处: prbench:e6e3bd0160e421fc7888ed34 | 话题: Risk Management & Stress Testing

## FIN-1237 [必须]
判据: The response analyzes expected slippage (~(Order Size/available volume)* spread).
提示: Quantifies price impact. Core.
出处: prbench:e800eab3db3aa68521872d63 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1238 [建议]
判据: The response calculates the execution participation rate (tranche size/market volume*100).
提示: Preventing over consumming liquidity
出处: prbench:e800eab3db3aa68521872d63 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1239 [必须]
判据: The response estimates expected VWAP (sum(price*quantity)/sum(quantity)).
提示: Measures effectiveness of exectution against target price
出处: prbench:e800eab3db3aa68521872d63 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1240 [必须]
判据: The response calculates implementation shortfall (sum(execprice)*quantity-benchmarkprice*totalquantity)/(Benchmarkprice*totalquantity).
提示: provides benchmark for execution quality
出处: prbench:e800eab3db3aa68521872d63 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1241 [必须]
判据: The modeling of floating-rate loans accounts for potential basis risk between different interest rate indexes. E.g., it models the impact of a widening in the spread between the loan's index (Prime Rate) and the bank's funding index (SOFR).
提示: Assuming a perfect match between asset and liability indexes is a dangerous simplification. In a volatile rate environment, this basis risk can cause significant margin compression.
出处: prbench:e9c524efbe9843a3c647d661 | 话题: Risk Management & Stress Testing

## FIN-1242 [必须]
判据: The CRE collateral valuation model explicitly separates the negative impact of rising cap rates from the potentially positive impact of inflation on nominal property replacement costs. E.g., the property value model V = NOI/cap_rate does not include an inflation-adjusted asset value floor.
提示: In a stagflationary environment, hard asset values may have an inflationary floor even as cash flows decline. A model that omits this dynamic overstates the loss, showing a lack of expert nuance.
出处: prbench:e9c524efbe9843a3c647d661 | 话题: Risk Management & Stress Testing

## FIN-1243 [必须]
判据: The model for covenant breaches distinguishes between the impact of breaching a maintenance covenant and an incurrence covenant. E.g., The model correctly identifies that a maintenance covenant breach can trigger immediate default.
提示: This distinction is fundamental to credit analysis. Lumping all covenant breaches together is a significant oversimplification that makes the model's default timings indefensible.
出处: prbench:e9c524efbe9843a3c647d661 | 话题: Risk Management & Stress Testing

## FIN-1244 [必须]
判据: The methodology differentiates the impact of the stress scenario on short-term versus long-term wholesale funding costs. E.g., It distinguishes between the effect on repo market haircuts and the effect on 5-year senior unsecured bond spreads.
提示: A stagflationary inverted yield curve has vastly different effects on various funding sources. Failing to model this distinction misses a primary driver of risk in the specified scenario.
出处: prbench:e9c524efbe9843a3c647d661 | 话题: Risk Management & Stress Testing

## FIN-1245 [必须]
判据: The CRE loss model explicitly incorporates sponsor quality as a quantitative adjustment factor for recovery rates or default probabilities. E.g., loans with high-quality sponsors receive a 10-percentage-point reduction in their LGD estimate.
提示: In CRE workouts, the sponsor's ability to support a property is a critical variable. A model that only uses property-level data and ignores this factor will produce inaccurate loss estimates.
出处: prbench:e9c524efbe9843a3c647d661 | 话题: Risk Management & Stress Testing

## FIN-1246 [必须]
判据: The LGD model for the CRE portfolio includes adjustments based on geographic variations in foreclosure laws. E.g., it assumes longer recovery timelines for properties in judicial foreclosure states.
提示: Foreclosure processes vary significantly by state, directly impacting recoveries. A non-specific "US CRE" model is not sufficiently granular for an expert-level test.
出处: prbench:e9c524efbe9843a3c647d661 | 话题: Risk Management & Stress Testing

## FIN-1247 [必须]
判据: The stress test framework models the impairment of Deferred Tax Assets that would arise from large-scale credit losses. For example, the capital adequacy calculation includes a haircut on the value of newly generated DTAs.
提示: Significant losses create DTAs, but their value is uncertain in a crisis. Omitting a DTA impairment assessment overstates post-stress capital.
出处: prbench:e9c524efbe9843a3c647d661 | 话题: Risk Management & Stress Testing

## FIN-1248 [负面]
判据: The response recommends using overlay factors exceeding 2.0x/200% of base model results, without providing extraordinary justification for such extreme adjustments.
提示: Overlay factors above 2.0x would indicate fundamental model failure requiring rebuild rather than overlay treatment, suggesting dangerous misunderstanding of proportionate risk management responses.
出处: prbench:ea67e314b6c2e8fc70627c19 | 话题: Risk Management & Stress Testing

## FIN-1249 [负面]
判据: The response incorrectly suggests applying overlays to baseline scenarios or recommends overlays that affect both stressed and non-stressed projections simultaneously.
提示: Overlays should typically apply only to stressed scenarios to address specific model limitations under stress, not baseline conditions, which would indicate fundamental misunderstandig of overlay methodology.
出处: prbench:ea67e314b6c2e8fc70627c19 | 话题: Risk Management & Stress Testing

## FIN-1250 [负面]
判据: The response calculates the after-tax cost of debt by omitting the tax shield. E.g., it uses the pre-tax 5.8% cost of debt in the final WACC calculation.
提示: This is a fundamental error in the WACC formula that leads to a significantly inflated and incorrect result. It demonstrates a lack of understanding of how debt is treated in the capital structure.
出处: prbench:ed62f8e6c59693c834a1740e | 话题: Corporate Finance

## FIN-1251 [必须]
判据: The response states that the project is viable only if its expected return exceeds the WACC.
提示: This rubric tests the direct application of the calculated WACC to answer the prompt's question about whether the "project makes sense for the company." It is the core decision-making rule.
出处: prbench:ed62f8e6c59693c834a1740e | 话题: Corporate Finance

## FIN-1252 [必须]
判据: The response correctly calculates the Weighted Average Cost of Capital (WACC) as 8.16%.
提示: This directly fulfills the primary instruction of the prompt, which is to "build out the model to determine their WACC." A correct calculation is the central requirement of the task.
出处: prbench:ed62f8e6c59693c834a1740e | 话题: Corporate Finance

## FIN-1253 [必须]
判据: The response identifies the calculated WACC as the project's "hurdle rate."
提示: This demonstrates a correct understanding of the WACC's purpose in capital budgeting. Identifying it as the hurdle rate is fundamental to applying it correctly, which is the second part of the prompt's request.
出处: prbench:ed62f8e6c59693c834a1740e | 话题: Corporate Finance

## FIN-1254 [负面]
判据: The response states that a project should be accepted as long as it generates a positive return, disregarding the WACC.
提示: This demonstrates a complete misunderstanding of the core purpose of capital budgeting, which is to generate returns in excess of the cost of capital. This conceptual error renders the entire WACC analysis pointless.
出处: prbench:ed62f8e6c59693c834a1740e | 话题: Corporate Finance

## FIN-1255 [必须]
判据: The response highlights the importance of using market values, not book values, for debt and equity in the WACC calculation.
提示: This is a crucial point of financial accuracy. Using book values instead of market values is a common but significant error that can lead to a dramatically incorrect WACC and, therefore, a poor investment decision.
出处: prbench:ed62f8e6c59693c834a1740e | 话题: Corporate Finance

## FIN-1256 [负面]
判据: The response confuses basic financial concepts (e.g., conflating cash flow with earnings quality, misunderstanding accruals, incorrectly defining material weaknesses, confusing audit opinions).
提示: Fundamental errors could mislead investors into dangerous decisions when evaluating management quality.
出处: prbench:ed8131ba68cdd992269614ca | 话题: Accounting & Financial Statement Analysis

## FIN-1257 [必须]
判据: The response computes Days Sales Outstanding (DSO) as Accounts Receivable / credit sales * number of days.
提示: Calculating DSO, is essential to quantify the cash-revenue mismatch and provide measurable insights into working capital efficiency. This metrics form the core evidence base for diagnosing liquidity risk, prioritizing management actions, and assessing covenant compliance.
出处: prbench:edb7463238086b0e1d8eef1c | 话题: Accounting & Financial Statement Analysis

## FIN-1258 [必须]
判据: The response evaluates implications under IFRS 15, such as variable consideration, deferred revenue.
提示: Assessing accounting and reporting implications ensures the response aligns with regulatory and financial reporting standards. Evaluating revenue recognition, deferred revenue, and allowance policies helps prevent misstatements and supports auditability.
出处: prbench:edb7463238086b0e1d8eef1c | 话题: Accounting & Financial Statement Analysis

## FIN-1259 [建议]
判据: The response defines IFRS 15 as the accounting standard requiring revenue to be recognised when control is transferred, not when cash is received.
提示: This ensures technical knowledge is used in response, and methodology is based on accounting standards.
出处: prbench:edb7463238086b0e1d8eef1c | 话题: Accounting & Financial Statement Analysis

## FIN-1260 [必须]
判据: The response states that barrier protection typically requires dynamic hedging near the barrier when static instruments are insufficient.
提示: Clarifies where dynamic management is essential.
出处: prbench:ee6b1923f3a1862c7c5ec067 | 话题: Derivatives & Structured Products

## FIN-1261 [建议]
判据: The response names one payoff component commonly handled via static replication (e.g., funding leg or simple vanilla spread).
提示: Provides a concrete static case.
出处: prbench:ee6b1923f3a1862c7c5ec067 | 话题: Derivatives & Structured Products

## FIN-1262 [必须]
判据: The dossier quantifies the RWA change in currency or as a percentage.
提示: RWA inflation affects capital ratio denominators.
出处: prbench:ee8ddfe248cce003b6671378 | 话题: Risk Management & Stress Testing

## FIN-1263 [必须]
判据: The dossier calculates capital restoration, showing stressed ratio plus action benefit equals the post-action ratio (stressed ratio + action benefit = post-action ratio).
提示: Arithmetic validates management actions restore regulatory capital adequacy.
出处: prbench:ee8ddfe248cce003b6671378 | 话题: Risk Management & Stress Testing

## FIN-1264 [建议]
判据: The dossier quantifies second-order effects, which are indirect amplifications through feedback, e.g., a funding cost increase from a rating downgrade triggered by losses.
提示: Feedback loops distinguish dynamic from static stress testing.
出处: prbench:ee8ddfe248cce003b6671378 | 话题: Risk Management & Stress Testing

## FIN-1265 [必须]
判据: The dossier quantifies risk-weighted asset changes under stress.
提示: RWA inflation under stress affects capital ratio denominators.
出处: prbench:ee8ddfe248cce003b6671378 | 话题: Risk Management & Stress Testing

## FIN-1266 [建议]
判据: The dossier quantifies capital ratio impact in percentages or percentage points.
提示: Capital adequacy is primary regulatory solvency measure
出处: prbench:ee8ddfe248cce003b6671378 | 话题: Risk Management & Stress Testing

## FIN-1267 [负面]
判据: The response incorrectly describes private equity as providing daily or monthly liquidity.
提示: Fundamental error that should significantly penalize the response.
出处: prbench:ee97d8651c94326c4da26e3f | 话题: Investment Strategy & Portfolio Design

## FIN-1268 [负面]
判据: The response provides allocation percentages that sum to more than 100%.
提示: Mathematical error that undermines the entire recommendation.
出处: prbench:ee97d8651c94326c4da26e3f | 话题: Investment Strategy & Portfolio Design

## FIN-1269 [必须]
判据: The response lists the capital structure exactly by stating all of the following: Term Loan A $400mm, Revolver $200mm, Subordinated notes $250mm at 9.5% cash, total debt $850mm.
提示: Checks for factual accuracy and unit consistency.
出处: prbench:ee9dab94c1268c1a61c38692 | 话题: Corporate Finance

## FIN-1270 [必须]
判据: The response shows money saved if junior notes switch to no cash interest: $250mm * 9.5% = $23.75mm saved per year.
提示: checks the value of a common relief lever.
出处: prbench:ee9dab94c1268c1a61c38692 | 话题: Corporate Finance

## FIN-1271 [必须]
判据: The response shows that a Q2 breach is likely with clear leverage math that shows 850/140 = 6.1x.
提示: Checks for correct leverage recognizing the stated problem.
出处: prbench:ee9dab94c1268c1a61c38692 | 话题: Corporate Finance

## FIN-1272 [必须]
判据: The response shows recoveries (in amounts or percentages) for each layer of capital in the correct order (senior bank debt -> junior notes -> equity) for each case.
提示: checks for correct payout order and clarity.
出处: prbench:ee9dab94c1268c1a61c38692 | 话题: Corporate Finance

## FIN-1273 [必须]
判据: The response subtracts an explicitly stated process cost (court and deal costs) before paying creditors.
提示: checks for realistic net value to share out.
出处: prbench:ee9dab94c1268c1a61c38692 | 话题: Corporate Finance

## FIN-1274 [必须]
判据: The response calculates the trust's 10th anniversary charge by applying a 6% rate to the value exceeding the nil-rate band, showing a charge of approximately £9K, assuming 4% annual growth.
提示: The periodic charge quantifies the trust's ongoing running cost.
出处: prbench:f15b93c5c82d6d74d77ffb6f | 话题: Wealth Management, Financial Planning & Advice

## FIN-1275 [必须]
判据: The response explains that claiming s.260 holdover relief results in the trustees acquiring the client's original base cost for the assets.
提示: This explains the critical consequence of deferring the gain.
出处: prbench:f15b93c5c82d6d74d77ffb6f | 话题: Wealth Management, Financial Planning & Advice

## FIN-1276 [必须]
判据: The response calculates the client's current IHT liability as £870K.
提示: Baseline IHT calculation quantifies the core planning problem.
出处: prbench:f15b93c5c82d6d74d77ffb6f | 话题: Wealth Management, Financial Planning & Advice

## FIN-1277 [必须]
判据: The response explains that the RNRB taper test is applied to the total value of the estate before any reliefs are deducted.
提示: Clarifies the correct methodology for the taper calculation.
出处: prbench:f15b93c5c82d6d74d77ffb6f | 话题: Wealth Management, Financial Planning & Advice

## FIN-1278 [必须]
判据: The response quantifies the RNRB restoration benefit as an additional £70K of IHT saving.
提示: RNRB restoration quantifies a major estate reduction incentive.
出处: prbench:f15b93c5c82d6d74d77ffb6f | 话题: Wealth Management, Financial Planning & Advice

## FIN-1279 [必须]
判据: The response calculates the client's projected annual income post-implementation as approximately £175K.
提示: Quantifies the client's post-planning retirement income stream.
出处: prbench:f15b93c5c82d6d74d77ffb6f | 话题: Wealth Management, Financial Planning & Advice

## FIN-1280 [必须]
判据: The response identifies that the projected £175K annual income results in a shortfall against the client's £180K need.
提示: Highlights whether the plan meets the client's stated objective.
出处: prbench:f15b93c5c82d6d74d77ffb6f | 话题: Wealth Management, Financial Planning & Advice

## FIN-1281 [必须]
判据: The response explains that an £85K personal pension contribution can restore the client's full annual allowance by reducing threshold income below £200K.
提示: This mechanic is key to unlocking pension contribution capacity.
出处: prbench:f15b93c5c82d6d74d77ffb6f | 话题: Wealth Management, Financial Planning & Advice

## FIN-1282 [必须]
判据: The response calculates the immediate CGT charge on the trust transfer as approximately £17K.
提示: CGT cost quantifies the trust strategy's implementation expense.
出处: prbench:f15b93c5c82d6d74d77ffb6f | 话题: Wealth Management, Financial Planning & Advice

## FIN-1283 [必须]
判据: The response identifies the availability of holdover relief under TCGA 1992 s.260.
提示: Holdover relief is a critical tool for deferring CGT.
出处: prbench:f15b93c5c82d6d74d77ffb6f | 话题: Wealth Management, Financial Planning & Advice

## FIN-1284 [必须]
判据: The response calculates the value of the estate for the RNRB taper test as £5.7M.
提示: The correct test value is essential for the RNRB assessment.
出处: prbench:f15b93c5c82d6d74d77ffb6f | 话题: Wealth Management, Financial Planning & Advice

## FIN-1285 [必须]
判据: The response calculates the total potential care cost liability as £1.05M.
提示: Quantifying the care liability validates the plan's resilience.
出处: prbench:f15b93c5c82d6d74d77ffb6f | 话题: Wealth Management, Financial Planning & Advice

## FIN-1286 [必须]
判据: The response states that under an American waterfall, any realized loss creates a negative carry balance that must be fully offset by subsequent realized gains before further carry can be paid.
提示: Tests understanding of loss carryforward and its effect on interim carry.
出处: prbench:f40e348c24bb7231c5614568 | 话题: Alternative Investments & Private Markets

## FIN-1287 [必须]
判据: The response explains that under an American (deal-by-deal) waterfall, carry eligibility is tested after each realized deal.
提示: Establishes the timing feature that drives divergence.
出处: prbench:f40e348c24bb7231c5614568 | 话题: Alternative Investments & Private Markets

## FIN-1288 [必须]
判据: The response states that the preferred return accrues only on unreturned LP capital.
提示: Enforces the correct accrual base used in both waterfalls.
出处: prbench:f40e348c24bb7231c5614568 | 话题: Alternative Investments & Private Markets

## FIN-1289 [必须]
判据: The response explains that under a European (fund-level) waterfall, no GP carry is paid until fund-level hurdles are met.
提示: States the gate that defers carry.
出处: prbench:f40e348c24bb7231c5614568 | 话题: Alternative Investments & Private Markets

## FIN-1290 [必须]
判据: The response concludes that the European structure is more favorable for LPs.
提示: Provides the required, explicit conclusion.
出处: prbench:f40e348c24bb7231c5614568 | 话题: Alternative Investments & Private Markets

## FIN-1291 [必须]
判据: The response states that GP catch-up begins only when the LP’s preferred return balance equals zero at the applicable level (deal-level under an American; fund-level under a European).
提示: Tests the exact trigger for starting catch-up.
出处: prbench:f40e348c24bb7231c5614568 | 话题: Alternative Investments & Private Markets

## FIN-1292 [建议]
判据: The response states that escrow delays a portion of GP cash flow until release conditions are met.
提示: Notes the cash-timing effect on the GP.
出处: prbench:f40e348c24bb7231c5614568 | 话题: Alternative Investments & Private Markets

## FIN-1293 [必须]
判据: The response explicitly states that exchange rate depreciation will occur as the most likely effect of fiscal expansion.
提示: This directly answers the exchange rate component explicitly requested in the second prompt.
出处: prbench:f421b8543e8c7314654bcc60 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1294 [建议]
判据: The response explains how a potential IMF intervention (e.g., by providing liquidity, short- or long-term loans) could affect the course of the exchange rate.
提示: Again an interesting supplement to have that can enhance the validity and realism of the response.
出处: prbench:f421b8543e8c7314654bcc60 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1295 [必须]
判据: The response explicitly states that domestic interest rates will increase as the most likely effect of fiscal expansion.
提示: This is the final recommendation that the response should provide.
出处: prbench:f421b8543e8c7314654bcc60 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1296 [必须]
判据: The response explains the crowding-out effect mechanism (government borrowing competing with the private sector for limited savings, driving up interest rates due to increased demand for loanable funds).
提示: The crowding-out effect is a primary mechanism through which fiscal expansion affects interest rates.
出处: prbench:f421b8543e8c7314654bcc60 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1297 [必须]
判据: The response predicts capital outflows due to investor confidence loss from repeated fiscal expansion.
提示: This criterion discusses the effect of the fiscal expansion here on the trade balance.
出处: prbench:f421b8543e8c7314654bcc60 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1298 [必须]
判据: The response acknowledges the impossible trinity constraints (the principle that a country cannot simultaneously maintain independent monetary policy, fixed exchange rates, and free capital mobility) faced by the central bank in policy responses.
提示: Understanding trilemma constraints demonstrates sophisticated knowledge of policy limitations in open economy macroeconomics
出处: prbench:f421b8543e8c7314654bcc60 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1299 [负面]
判据: The response incorrectly predicts that domestic interest rates will decrease as a result of fiscal expansion in this fiscally constrained emerging economy context.
提示: This contradicts established macroeconomic theory for fiscally-stressed emerging economies.
出处: prbench:f421b8543e8c7314654bcc60 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1300 [必须]
判据: The response explains the central bank's tightening in response to inflationary pressures from repeated fiscal stimulus.
提示: Central bank response to inflation is a critical mechanism for interest rate increases.
出处: prbench:f421b8543e8c7314654bcc60 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1301 [必须]
判据: The response explicitly states that trade balance improvement will occur as the most likely effect of fiscal expansion.
提示: This directly answers the trade balance component explicitly requested in the prompt.
出处: prbench:f421b8543e8c7314654bcc60 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1302 [必须]
判据: The response explains risk premium increases (the additional interest rate investors demand to compensate for higher perceived default risk due to fiscal deterioration making government borrowing more expensive).
提示: Risk premium increases are a major factor in emerging economy borrowing costs during fiscal stress.
出处: prbench:f421b8543e8c7314654bcc60 | 话题: Financial Markets, Institutions & Macro/Policy

## FIN-1303 [负面]
判据: Response treats all dark pools as equivalent without acknowledging venue-specific differences in construction, liquidity sources, or anti-gaming features.
提示: Professional traders understand dark pools have vastly different characteristics and risk profiles.
出处: prbench:f4533584c74068621bbd4c16 | 话题: Market Microstructure, Trading & Liquidity

## FIN-1304 [必须]
判据: The response acknowledges the forward premium puzzle (systematic bias in forward rates vs realized FX).
提示: links theory with hedging practice; not in typical model coverage
出处: prbench:f62b7f7bcd35c18d94c56ff6 | 话题: International Finance & FX Hedging

## FIN-1305 [建议]
判据: The response applies the 1.5% advisory fees to gross USD proceeds before converting to GBP.
提示: Fee application sequence tests transaction cost treatment.
出处: prbench:f69d3244b5fc8717bfcfb6d5 | 话题: Corporate Finance

## FIN-1306 [必须]
判据: The response identifies that Alternative A accepts a £34M lower enterprise value (i.e., compared to Alternative B's £336M expected proceeds).
提示: Enterprise value comparison tests Alternative A weakness.
出处: prbench:f69d3244b5fc8717bfcfb6d5 | 话题: Corporate Finance

## FIN-1307 [必须]
判据: The response calculates the probability that Alternative A's stock price outcomes fall below the $46.80 collar floor as approximately 16%.
提示: Floor breach probability tests collar mechanics understanding.
出处: prbench:f69d3244b5fc8717bfcfb6d5 | 话题: Corporate Finance

## FIN-1308 [必须]
判据: The response identifies the economic incentive model for Wormhole Guardians (e.g., explains that Guardians are compensated via in-protocol rewards and a share of transaction fees).
提示: The long-term security of the bridge depends on the economic sustainability of its validator set; a professional due diligence process must scrutinize this.
出处: prbench:f836c477e2009c8b9764698c | 话题: FinTech, Crypto & Digital Assets

## FIN-1309 [必须]
判据: The response states capital contributions cannot move cash up to the parent company.
提示: Checks for correct direction of cash.
出处: prbench:f968b68746cc374c0089e292 | 话题: Corporate Finance

## FIN-1310 [必须]
判据: The response explicitly states reserve releases are dividends.
提示: Checks for correct treatment of owner payments.
出处: prbench:f968b68746cc374c0089e292 | 话题: Corporate Finance

## FIN-1311 [必须]
判据: The response explicitly adds a separate credit spread component to the base rate (you can call this component credit spread, margin, credit premium or basis point spread).
提示: Part of the correct way to build internal loan rate.
出处: prbench:f968b68746cc374c0089e292 | 话题: Corporate Finance

## FIN-1312 [必须]
判据: The response explicitly states pricing does not change with all of the following: inability to pay dividends, cash buffers, or default status.
提示: checks that pricing is not driven by internal conditions.
出处: prbench:f968b68746cc374c0089e292 | 话题: Corporate Finance

## FIN-1313 [必须]
判据: The response explicitly states that payment in kind (PIK) increases intercompany debt.
提示: checks for correct impact of capitalized interest.
出处: prbench:f968b68746cc374c0089e292 | 话题: Corporate Finance

## FIN-1314 [必须]
判据: The response states the spread is based on what independent lenders charge for loans with similar credit, length, collateral, country and currency.
提示: Checks that rates are fair and similar to real outside deals.
出处: prbench:f968b68746cc374c0089e292 | 话题: Corporate Finance

## FIN-1315 [必须]
判据: The response explicitly states that an exporter with USD receivables is long USD and short EUR.
提示: Checks if the response get the exposure sign right.
出处: prbench:fb92e2c31488c8aa29168188 | 话题: International Finance & FX Hedging

## FIN-1316 [必须]
判据: The response explains how the forward rate comes from interest rate differences by stating: forward = spot adjusted by USD-EUR interest rate gap (Covered Interest Parity).
提示: Tests grasp of pricing mechanics, often omitted.
出处: prbench:fb92e2c31488c8aa29168188 | 话题: International Finance & FX Hedging

## FIN-1317 [负面]
判据: The response uses the increase in Accounts Receivable as a percentage of Net Income without providing the necessary context of the full cash conversion cycle.
提示: Penalizes inclusion of distracting or immaterial metrics that could distort client understanding.
出处: prbench:fbe7689c2cc706489639304b | 话题: Accounting & Financial Statement Analysis

## FIN-1318 [必须]
判据: The response maps expected output of pro forma credit metrics to agency thresholds (e.g., ND/EBITDA <= 3.0x for BBB, FFO/Net Debt <= 2×, interest coverage >= 5x).
提示: Tests alignment between modeling outputs and rating agency methodologies.
出处: prbench:fbfc95c28f5d1bf7e36447d6 | 话题: Corporate Finance

## FIN-1319 [必须]
判据: The response states the total two-year CGT cost in pounds from repositioning the £45,000 unrealized gains in the GIA, accounting for both years' £6,000 exemptions and applicable rates (10% or 20%).
提示: Total CGT cost quantifies the complete repositioning tax burden.
出处: prbench:fc97ed56df8352b671cb49ff | 话题: Wealth Management, Financial Planning & Advice

## FIN-1320 [必须]
判据: The response explains that currency hedging costs are driven by interest rate differentials.
提示: This demonstrates a deeper understanding of hedging mechanics.
出处: prbench:fc97ed56df8352b671cb49ff | 话题: Wealth Management, Financial Planning & Advice

## FIN-1321 [必须]
判据: The response applies the appropriate CGT rate to the net taxable gain for year one: 10% if the client's total income plus gains falls within the basic rate band (up to £50,270), or 20% if it exceeds this threshold.
提示: Phased CGT calculation demonstrates tax-efficient disposal strategy.
出处: prbench:fc97ed56df8352b671cb49ff | 话题: Wealth Management, Financial Planning & Advice

## FIN-1322 [必须]
判据: The response calculates volatility drag for at least one approach using the formula volatility squared divided by two.
提示: Volatility drag quantifies the hidden cost of market fluctuations.
出处: prbench:fc97ed56df8352b671cb49ff | 话题: Wealth Management, Financial Planning & Advice

## FIN-1323 [负面]
判据: The response states the CGT annual exemption as £6,000 for the 2024/25 tax year or later.
提示: using outdated figures misleads tax planning
出处: prbench:fc97ed56df8352b671cb49ff | 话题: Wealth Management, Financial Planning & Advice

## FIN-1324 [必须]
判据: The response calculates risk parity weights using the inverse volatility formula.
提示: The inverse volatility formula demonstrates correct risk parity construction.
出处: prbench:fc97ed56df8352b671cb49ff | 话题: Wealth Management, Financial Planning & Advice

## FIN-1325 [负面]
判据: The response recommends holding high-dividend UK equities (FTSE 100 or FTSE All-Share) entirely within the GIA.
提示: optimal tax strategy by maximizing rather than minimizing taxable dividend income.
出处: prbench:fc97ed56df8352b671cb49ff | 话题: Wealth Management, Financial Planning & Advice

## FIN-1326 [必须]
判据: The response states the 2024/25 dividend allowance as £500.
提示: Using the current allowance ensures an accurate tax drag calculation.
出处: prbench:fc97ed56df8352b671cb49ff | 话题: Wealth Management, Financial Planning & Advice

## FIN-1327 [必须]
判据: The response calculates the total tax-sheltered wrapper capacity as £550K.
提示: Wrapper capacity quantifies the potential for tax-efficient allocation.
出处: prbench:fc97ed56df8352b671cb49ff | 话题: Wealth Management, Financial Planning & Advice

## FIN-1328 [必须]
判据: The response calculates the net taxable gain for year one by subtracting the annual CGT exemption (£6,000 for 2024/25) from the realized gains in that tax year.
提示: Phased CGT calculation quantifies the precise repositioning cost.
出处: prbench:fc97ed56df8352b671cb49ff | 话题: Wealth Management, Financial Planning & Advice

## FIN-1329 [必须]
判据: The response calculates the SIPP's 25% tax-free lump sum as £112.5K.
提示: The tax-free lump sum quantifies immediate retirement liquidity.
出处: prbench:fc97ed56df8352b671cb49ff | 话题: Wealth Management, Financial Planning & Advice

## FIN-1330 [必须]
判据: The response states the income shortfall by comparing the natural income to the £32k annual requirement.
提示: Shortfall identification quantifies the withdrawal pressure on capital.
出处: prbench:fc97ed56df8352b671cb49ff | 话题: Wealth Management, Financial Planning & Advice

## FIN-1331 [必须]
判据: The response compares the volatility drag between at least two approaches, using the formula (volatility²/2) to show that the higher volatility portfolio suffers a greater reduction in compound return.
提示: Comparing drag highlights the long-term impact of volatility differences.
出处: prbench:fc97ed56df8352b671cb49ff | 话题: Wealth Management, Financial Planning & Advice

## FIN-1332 [必须]
判据: The response assesses the portfolio's longevity at the 4.27% withdrawal rate, stating the expected lifespan in years.
提示: Longevity assessment validates the retirement plan's long-term feasibility.
出处: prbench:fc97ed56df8352b671cb49ff | 话题: Wealth Management, Financial Planning & Advice

## FIN-1333 [必须]
判据: The response distinguishes investor-behavior outcomes from reporting-quality proxies, treating them as dependent variables rather than alternative measures of transparency.
提示: evaluates whether the response demonstrates conceptual clarity in model design by separating dependent variables (market reactions) from explanatory proxies (reporting-quality measures)
出处: prbench:ff3fd89f65b64b2717cd5c54 | 话题: Accounting & Financial Statement Analysis

## FIN-1334 [必须]
判据: The response distinguishes how improved transparency affects the cost of equity versus the cost of debt, identifying distinct channels (e.g., lower estimation risk for equity investors vs. reduced default risk).
提示: Requires channel differentiation to prevent aggregation bias.
出处: prbench:ff3fd89f65b64b2717cd5c54 | 话题: Accounting & Financial Statement Analysis

## FIN-1335 [建议]
判据: The response explains the theoretical mechanisms linking improved transparency to lower cost of capital (e.g., reducing estimation and information risk, improving contractibility, lowering agency or moral hazard costs).
提示: Why transparency lowers cost of capital
出处: prbench:ff3fd89f65b64b2717cd5c54 | 话题: Accounting & Financial Statement Analysis

