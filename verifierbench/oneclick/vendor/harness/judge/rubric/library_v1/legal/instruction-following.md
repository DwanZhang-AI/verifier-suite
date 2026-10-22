# legal / Instruction Following(143 条)

## LEG-0605 [必须]
判据: The response is presented in a formal legal opinion format (e.g., Background/Facts, Issues Presented, Applicable Law, Analysis, Recommendations, Conclusion).
提示: the correct mode of presentation
出处: prbench:0b5d54ce56ae81dd77ad5465 | 话题: Litigation & Dispute Resolution

## LEG-0606 [必须]
判据: NO CHANGE.
提示: This clarifies what counts as fair and reasonable.
出处: prbench:15440656db57ea7d6ade5b58 | 话题: Family Law

## LEG-0607 [必须]
判据: The response generates the requested legal document, i.e., a memorandum of less than 1,000 words.
提示: This is an explicit request of the user.
出处: prbench:1597f3dc6d2bf87c3f64bf54 | 话题: Regulatory & Administrative Law

## LEG-0608 [必须]
判据: The response includes a risk matrix that lists at least three required columns, e.g., (1) civil and criminal liability categories (e.g., conversion, breach of contract, theft/unjust enrichment), (2) likelihood of each risk, and (3) mitigation steps.
提示: Replaces vague language like “complete” with explicit, measurable components, ensuring graders can confirm whether all required dimensions appear without subjective judgment.
出处: prbench:1597f3dc6d2bf87c3f64bf54 | 话题: Regulatory & Administrative Law

## LEG-0609 [负面]
判据: The response contains unexplained jargon (e.g., DCTF, ECD/ECF).
提示: Jargons without explanation can confuse the user.
出处: prbench:18c1e2e076732e6c29f56cab | 话题: Corporate & Transactional Law

## LEG-0610 [必须]
判据: Except for proper names, the response is fully in English.
提示: Is important writen in the same language of user.
出处: prbench:18c1e2e076732e6c29f56cab | 话题: Corporate & Transactional Law

## LEG-0611 [必须]
判据: The model explains the alternatives to deportation using plain language.
提示: The model should answer using plain language as it can be inferred from the prompt that the user is not an expert.
出处: prbench:19a69e86cd6e81eba2e65e6a | 话题: Regulatory & Administrative Law

## LEG-0612 [负面]
判据: The response cites case law decided by a non-Florida court.
提示: The user asked the model to cite Florida law, so the model should be penalized for citing case law outside this jurisdiction.
出处: prbench:1cbcf6cfb73d7245f87d65f9 | 话题: Family Law

## LEG-0613 [必须]
判据: The model explains the concept of proprietary estoppel in plain language.
提示: The model should answer using simplified concepts as it can be inferred from the prompt that the user is not an expert.
出处: prbench:1ee9b18ac8696ab2ad366eee | 话题: Real Estate & Property Law

## LEG-0614 [负面]
判据: Response suggests a clause in question 4 that is not related to covering the SRL for a potential breach due to non‑payment.
提示: The prompt mentioned that the clauses that the LLM should propose have to be limited to covering the Romanian SRL to an eventual breach of the contract for non-payment.
出处: prbench:21fb45276fcbf983ddc5f367 | 话题: Corporate & Transactional Law

## LEG-0615 [必须]
判据: Response states that the French company has an intra-community VAT number.
提示: Tha'ts why using the French company became interesting.
出处: prbench:21fb45276fcbf983ddc5f367 | 话题: Corporate & Transactional Law

## LEG-0616 [建议]
判据: The response includes an overview of the answers (a summary listing each of the 4 questions).
提示: Standard in executive summaries.
出处: prbench:21fb45276fcbf983ddc5f367 | 话题: Corporate & Transactional Law

## LEG-0617 [必须]
判据: The response is drafted as an executive summary (e.g., To, From, Date, Subject).
提示: This is the whole point of the prompt.
出处: prbench:21fb45276fcbf983ddc5f367 | 话题: Corporate & Transactional Law

## LEG-0618 [建议]
判据: Response recognizes that the leadership has already decided to use the Romanian company.
提示: Just to remember the previous decision to the leadership.
出处: prbench:21fb45276fcbf983ddc5f367 | 话题: Corporate & Transactional Law

## LEG-0619 [必须]
判据: The response only cites case law decided by the Second District Court of Appeal or the Florida Supreme Court.
提示: The user asked the model to only cite binding case law. This criterion ensures the model follows this constraint.
出处: prbench:224bcf8667d3ff5b1f59cbd7 | 话题: Real Estate & Property Law

## LEG-0620 [必须]
判据: The model explains the criteria of easements using plain language.
提示: The model should answer using plain language as it can be inferred from the prompt that the user is not an expert.
出处: prbench:2aa6b3a20e7358163d83e5b0 | 话题: Real Estate & Property Law

## LEG-0621 [负面]
判据: Provides excessive procedural detail (e.g., long step-by-step "fact-finding" phases instead of addressing ownership of AI output directly).
提示: Overloads multi-step strategies instead of focusing on the concrete legal issue at hand.
出处: prbench:317328a83d8426b22e79c61c | 话题: Intellectual Property (IP) Law

## LEG-0622 [必须]
判据: Explicitly addresses the impact of reporting on racial or ethnic pay disparities.
提示: Raises the analysis beyond gender bias, fulfilling the requirement to address systemic gender and racial disparities, crucial for modern consulting.
出处: prbench:318f92b38d6194c262c8a727 | 话题: Labor & Employment Law

## LEG-0623 [建议]
判据: The response presents a clear, tripartite structure, with distinct sections dedicated to (e.g., Comparative Analysis, Methodological Critique, and Next-Generation Policies).
提示: Ensures the response maintains the rigor and clarity of a high-level strategic consulting document, addressing all facets of the prompt.
出处: prbench:318f92b38d6194c262c8a727 | 话题: Labor & Employment Law

## LEG-0624 [必须]
判据: The response asks the court to deny sanctions under Rule 37(e)(2).
提示: Ensures correct procedural close.
出处: prbench:3404664b7048e68c9b576681 | 话题: Litigation & Dispute Resolution

## LEG-0625 [必须]
判据: Each section evaluates the likelihood of success as "high", "moderate", or "low".
提示: The likelihood of success is ultimately what the man is looking for and that answer should be provided.
出处: prbench:34d565f6b3fc2d978f7fcb11 | 话题: Regulatory & Administrative Law

## LEG-0626 [建议]
判据: The response adheres to the word count of the requested rationale for the legal state of Polymarket within the United States, i.e., 500 words.
提示: Requested but not as important.
出处: prbench:36dde97eee20c83b61f884e0 | 话题: Regulatory & Administrative Law

## LEG-0627 [必须]
判据: The response provides the requested document, i.e., a legal memorandum.
提示: Explicit request of the user.
出处: prbench:36dde97eee20c83b61f884e0 | 话题: Regulatory & Administrative Law

## LEG-0628 [建议]
判据: The response adheres to the word count of the requested memo, i.e., 750 words.
提示: Requested, but not important.
出处: prbench:36dde97eee20c83b61f884e0 | 话题: Regulatory & Administrative Law

## LEG-0629 [建议]
判据: The response advises notifying parents and teachers only after the School Board has formally ratified the calendar amendment.
提示: Tests one distinct procedural sequence; verifiable and self-contained.
出处: prbench:3c6df467f3cf8b1f592b357d | 话题: Regulatory & Administrative Law

## LEG-0630 [必须]
判据: Response identifies information rights, dictating what business and financial information the company must provide to the investor, as a key protective clause.
提示: adds valuable, practical context to the founder-investor relationship
出处: prbench:439c72782c6da8b292136c81 | 话题: Corporate & Transactional Law

## LEG-0631 [必须]
判据: Response identifies board of directors' rights, which define the board's composition, as a key protective clause.
提示: board composition clause is critical because it defines who has ultimate control over the company's high-level strategy
出处: prbench:439c72782c6da8b292136c81 | 话题: Corporate & Transactional Law

## LEG-0632 [必须]
判据: Response identifies rights on share transfers, which control when and how shareholders can sell their stock, as a key protective clause.
提示: rules governing stock sales are a core part of any shareholder agreement.
出处: prbench:439c72782c6da8b292136c81 | 话题: Corporate & Transactional Law

## LEG-0633 [建议]
判据: Uses expert-level terminology (for example, "opposition period", "Diario Oficial", "INIC", or "INVIMA").
提示: The response should employ terms like "opposition period," "Diario Oficial," or "INIC" appropriately for an expert audience, assuming familiarity.
出处: prbench:468c21fce109b6ca17e7e236 | 话题: Intellectual Property (IP) Law

## LEG-0634 [必须]
判据: The response includes a formal greeting (e.g., “Dear [Name]”) and a professional closing (e.g., “Yours truly,” or “Sincerely,”).
提示: Converts “professional tone” into measurable, checkable form through objective markers.
出处: prbench:478c868103328eebe630defd | 话题: Real Estate & Property Law

## LEG-0635 [必须]
判据: The response limits legal explanations to one concise sentence per legislative citation.
提示: Ensures conciseness and avoids unnecessary elaboration without requiring tone interpretation.
出处: prbench:478c868103328eebe630defd | 话题: Real Estate & Property Law

## LEG-0636 [必须]
判据: The response includes section headings labeled “Facts,” “Law/Analysis,” and “Conclusion.”
提示: Lists required headings directly to make the rubric self-contained and verifiable.
出处: prbench:478c868103328eebe630defd | 话题: Real Estate & Property Law

## LEG-0637 [必须]
判据: D'Angelo citation in requested format "D'Angelo v Chamberlain, 2021 CanLII 139416 (LTB)".
提示: correct canlii citation format per user
出处: prbench:478c868103328eebe630defd | 话题: Real Estate & Property Law

## LEG-0638 [必须]
判据: The response contains a sentence expressing openness to negotiation, such as “We remain open to discussing a resolution” or “Please advise if you wish to propose settlement terms.”
提示: Unknown, but possible instruction from client
出处: prbench:478c868103328eebe630defd | 话题: Real Estate & Property Law

## LEG-0639 [必须]
判据: Reference is made to the dismissal of the initial N13 on the basis of the date (i.e., stale-dated to November 2024).
提示: It could be a bit vague, but this is a critical basis on which the procedural history turns.
出处: prbench:478c868103328eebe630defd | 话题: Real Estate & Property Law

## LEG-0640 [必须]
判据: The response expressly states that the client refuses repayment of compensation in clear, professional terms.
提示: critical fact as this was catalyst to dispute
出处: prbench:478c868103328eebe630defd | 话题: Real Estate & Property Law

## LEG-0641 [必须]
判据: The response begins with a short paragraph summarizing key facts and referencing s. 209(2) as the primary argument.
提示: Essential part of procedural history and reference to further overlooked steps per prompt guidelines.
出处: prbench:478c868103328eebe630defd | 话题: Real Estate & Property Law

## LEG-0642 [必须]
判据: The response mentions at least one CVM or CGU precedent on whistleblower protection or internal reporting irregularities (e.g., Decree No. 10,153/2019, Instruction No. 607/2019).
提示: This enhances familiarity with real-world administrative decisions.
出处: prbench:4b8004b681706984433657c7 | 话题: Legal Ethics, Compliance & Risk Management

## LEG-0643 [必须]
判据: The response maintains a coherent memo structure, e.g. Facts, Issues, Law, Analysis, and Conclusion.
提示: Includes clear memo sections.
出处: prbench:4bfbd26a7dc1398c2675fff5 | 话题: Labor & Employment Law

## LEG-0644 [必须]
判据: The response must maintain focus on legal frameworks and analysis, not prescriptive drafting or step-by-step instructions.
提示: Ensures compliance with guidelines against direct legal advice or templates for filing.
出处: prbench:501440896678bfb34627c648 | 话题: Litigation & Dispute Resolution

## LEG-0645 [必须]
判据: The response does not provide extraneous information (e.g., the cancellation and suspension distinction issue or the substantive appeal issues).
提示: User is confused and specifically asked the model to focus on this aspect of the interim assistance Order issue (per prior conversations and final).
出处: prbench:54e1e4d5570867dbb4bd565a | 话题: Regulatory & Administrative Law

## LEG-0646 [必须]
判据: The response is structured into the three requested sections/bullets: (1) law and policy regime for interim assistance, (2) other interim powers to benefit the appellant, and (3) whether ODSP may refuse and the strongest case for a duty to comply.
提示: It satisfies the prompt's instructions.
出处: prbench:54e1e4d5570867dbb4bd565a | 话题: Regulatory & Administrative Law

## LEG-0647 [必须]
判据: The response presents a concise factual background organised as “before, during, and after” the mass exodus.
提示: Provides a proper structure for the background of the case.
出处: prbench:551badd04b77ad85e346e655 | 话题: International Law & Trade

## LEG-0648 [必须]
判据: The response recognizes the mass exodus of approximately 100,000 ethnic Armenians from Nagorno-Karabakh (Azerbaijan) to Armenia.
提示: The response understands the factual trigger for ICC communication
出处: prbench:551badd04b77ad85e346e655 | 话题: International Law & Trade

## LEG-0649 [必须]
判据: The response generates the requested legal document, i.e., a memorandum.
提示: Explicit request of the user.
出处: prbench:560ddd56555e647aeb48715b | 话题: Regulatory & Administrative Law

## LEG-0650 [建议]
判据: The response adheres to the word count of the legal document, i.e., 750 words.
提示: Requested by the user, not too important for it to be exact adherence.
出处: prbench:560ddd56555e647aeb48715b | 话题: Regulatory & Administrative Law

## LEG-0651 [建议]
判据: The response adheres to the word count of the legal document requested, i.e., 750 words.
提示: Not too important, but nice to make sure not too long.
出处: prbench:5b75d74ee456aad165158ed0 | 话题: Labor & Employment Law

## LEG-0652 [建议]
判据: The response generates the legal document requested by the user, i.e., a memorandum.
提示: Explicit request from the user.
出处: prbench:5b75d74ee456aad165158ed0 | 话题: Labor & Employment Law

## LEG-0653 [必须]
判据: The response complies with the prompt’s formatting instruction by presenting analysis in continuous paragraph form without headers, bullet points, lists, charts, or similar formatting.
提示: This is a specific ask in the prompt.
出处: prbench:5e55b0517dddde7548a4b66a | 话题: Regulatory & Administrative Law

## LEG-0654 [必须]
判据: The response contains the exact phrase our shared problem, common adversary, or mutual threat.
提示: This reframing is a sophisticated negotiation tactic that aligns the parties' interests.
出处: prbench:60e8ee630db78dfe84d3e12c | 话题: Litigation & Dispute Resolution

## LEG-0655 [必须]
判据: The response cites at least one disciplinary tribunal decision or NBA enforcement action against a lawyer for unauthorized practice in Nigeria.
提示: Requires knowledge of little-publicized administrative/disciplinary cases.
出处: prbench:66849580b472c84e371b4760 | 话题: Legal Ethics, Compliance & Risk Management

## LEG-0656 [必须]
判据: The response cites at least one Body of Benchers regulation related to admission or discipline.
提示: Models often overlook sub-regulations.
出处: prbench:66849580b472c84e371b4760 | 话题: Legal Ethics, Compliance & Risk Management

## LEG-0657 [必须]
判据: The response references at least one Nigerian case or disciplinary precedent addressing unauthorized practice of law.
提示: Precedents in this area are niche.
出处: prbench:66849580b472c84e371b4760 | 话题: Legal Ethics, Compliance & Risk Management

## LEG-0658 [建议]
判据: The response uses clear language for a small business owner without IP expertise.
提示: A non-expert user cannot apply complex legal advice unless it is communicated plainly.
出处: prbench:6698eef0d811b3d20b53bc8c | 话题: Intellectual Property (IP) Law

## LEG-0659 [必须]
判据: The response provides another mode of establishing an FTZE, which includes companies incorporated under CAMA registering as an FTZE.
提示: It provides an answer which satisfies the prompt constraints.
出处: prbench:6782f01eaeacc7b916c6e323 | 话题: International Law & Trade

## LEG-0660 [负面]
判据: The response overexplains procedural steps (e.g., long narratives of litigation strategy) instead of focusing on substantive law.
提示: Distracts from the legal analysis required.
出处: prbench:68aaae0ec299bd861e16efe6 | 话题: Corporate & Transactional Law

## LEG-0661 [必须]
判据: The response includes a defense that is sometimes used: that the fiduciary violation occurred "post-resignation," meaning they did not owe a fiduciary duty.
提示: This is an important defense.
出处: prbench:68aaae0ec299bd861e16efe6 | 话题: Corporate & Transactional Law

## LEG-0662 [必须]
判据: The response cites City of West Palm Beach v. Roberts, 72 So. 3d 294 (Fla. 4th DCA 2011).
提示: This criterion provides pertinent case law that the user requested.
出处: prbench:698e06d8e354efd32b1c0e87 | 话题: Constitutional & Civil Rights Law

## LEG-0663 [必须]
判据: Response does not provide any scripted phrases.
提示: The lawyer has specifically requested the model not advise them in such a manner
出处: prbench:6a1e030e837ddee286cfb948 | 话题: Legal Ethics, Compliance & Risk Management

## LEG-0664 [必须]
判据: Provides the bolded headings in the order outlined by the user.
提示: The user has specified the order and it should be followed for review and ease
出处: prbench:6a1e030e837ddee286cfb948 | 话题: Legal Ethics, Compliance & Risk Management

## LEG-0665 [必须]
判据: Refers to the Federation of Law Societies of Canada Model Code Rule 5.1-5.
提示: This is the rule related to a lawyer who unknowingly does or fails to do something that leads to a breach of the general rule of 5.1 (candour). In the context of this scenario, the lawyer has unknowingly caused the client to perjure, and the lawyer is ethically responsible for that perjury.
出处: prbench:6a1e030e837ddee286cfb948 | 话题: Legal Ethics, Compliance & Risk Management

## LEG-0666 [建议]
判据: The response refers to the motion.
提示: The lawyer seems to not be interested in knowing more about the motion in requesting the motion itself
出处: prbench:6a1e030e837ddee286cfb948 | 话题: Legal Ethics, Compliance & Risk Management

## LEG-0667 [必须]
判据: Cites the case Meek v. Flemming (1961).
提示: This is the judicial test for determining whether the nature of a given perjury qualifies as significant enough for a counsel to motion for withdrawal
出处: prbench:6a1e030e837ddee286cfb948 | 话题: Legal Ethics, Compliance & Risk Management

## LEG-0668 [必须]
判据: The response provides the requested legal documents for the user, i.e., legal memoranda.
提示: Direct request of the user.
出处: prbench:710dfb8fd3fb9c452657fe6c | 话题: Legal Ethics, Compliance & Risk Management

## LEG-0669 [建议]
判据: The response presents its analysis within a limit of 750 words.
提示: This an an explicit request, but not indispensable.
出处: prbench:71a8b074d7ed5556d56456be | 话题: International Law & Trade

## LEG-0670 [必须]
判据: The response includes all the essential components of a standard memo, including the purpose, facts, analysis and conclusion.
提示: The ensures that the key issues raised by the user are properly addressed.
出处: prbench:71a8b074d7ed5556d56456be | 话题: International Law & Trade

## LEG-0671 [必须]
判据: The response structures its analysis in the format of a legal memorandum, including date, subject line, author and recipient.
提示: This is the requested document by the user.
出处: prbench:71a8b074d7ed5556d56456be | 话题: International Law & Trade

## LEG-0672 [建议]
判据: The response acknowledges the fact that Brazil has requested dispute consultations with the U.S. under the WTO dispute settlement process.
提示: This acknowledgment of one of the explict mentions in the prompt sets the stage for further discussion of the possible impact of the consulatations.
出处: prbench:71a8b074d7ed5556d56456be | 话题: International Law & Trade

## LEG-0673 [必须]
判据: The response must provide specific legal terminology (res judicata, mutamento delle circostanze).
提示: Tests depth of knowledge; adds nuance.
出处: prbench:744a80be6643e7685d6639d4 | 话题: Family Law

## LEG-0674 [负面]
判据: The response includes a description of the role of AGU-SAI (or AGU generally), asserting that it serves as the central coordinating entity (quarterback) for all of Brazil's international litigation, including the WTO track.
提示: While AGU is crucial for defense, naming "AGU-SAI" as the de facto coordinator for all international litigation (especially the WTO track, led by Itamaraty) is a significant inaccuracy regarding the Brazilian government's jurisdictional structure.
出处: prbench:746556b5dbcffcf3971c2df8 | 话题: International Law & Trade

## LEG-0675 [必须]
判据: The response adheres to the stipulated word count for the legal document, i.e., within +/-10% of 500 words.
提示: Explicit request but not too important.
出处: prbench:77d6bfcff51f06c83bd495a2 | 话题: Regulatory & Administrative Law

## LEG-0676 [必须]
判据: The response is structured as a Legal Memorandum, including at least four of the following labeled sections: To/From/Date/Re, Issue, Facts, Analysis, or Conclusion.
提示: Explicit request by the user.
出处: prbench:77d6bfcff51f06c83bd495a2 | 话题: Regulatory & Administrative Law

## LEG-0677 [必须]
判据: The response mentions the differences between US rules and Brazilian rules in reporting fellow attorney misconduct.
提示: This is one of the key differences that must be mentioned here for risk of malpractice or breaking rules.
出处: prbench:78012abec329cec31fe67f66 | 话题: Legal Ethics, Compliance & Risk Management

## LEG-0678 [必须]
判据: The response cites case law only from the Third District Court of Appeal, the Florida Supreme Court, or the U.S. Supreme Court.
提示: This criterion ensures the model follows the user's direction to cite binding case law.
出处: prbench:7ba586bea5228e36d3a10360 | 话题: Criminal Law

## LEG-0679 [负面]
判据: The response recommends conceding statutory protections, e.g., "it is acceptable to reduce tax survival to 2 years".
提示: This is factually wrong.
出处: prbench:7e85e6f76f1f7bb25b5e0cf2 | 话题: Corporate & Transactional Law

## LEG-0680 [负面]
判据: The response presents more than 700 words.
提示: Dense texts could be boring.
出处: prbench:7e85e6f76f1f7bb25b5e0cf2 | 话题: Corporate & Transactional Law

## LEG-0681 [必须]
判据: The response begins with a short answer, for example, "short answer".
提示: This ensures the model follows the required structure and sets context immediately.
出处: prbench:7e85e6f76f1f7bb25b5e0cf2 | 话题: Corporate & Transactional Law

## LEG-0682 [负面]
判据: The response includes Portuguese terms without translation, for example, "jeitinho brasileiro".
提示: It can confuse the reader.
出处: prbench:7e85e6f76f1f7bb25b5e0cf2 | 话题: Corporate & Transactional Law

## LEG-0683 [必须]
判据: The email explains that the fact that the attorney has a good track record of obtaining emergency protective orders in the superior court makes this the best course of action for the client.
提示: This was requested in the prompt and is one of the main purposes of the email.
出处: prbench:80e434dee8c7e108bfa66d32 | 话题: Family Law

## LEG-0684 [必须]
判据: The email explains that the client would have strong arguments on appeal in spite of the holding in D.B. that preliminary orders are not moot.
提示: This is stated in the prompt and is the main point to be communicated in the email.
出处: prbench:80e434dee8c7e108bfa66d32 | 话题: Family Law

## LEG-0685 [必须]
判据: The email explains that pursuing dependency in juvenile court through DFCS would be unlikely to produce cost savings to the client because of the unpredictability.
提示: This was requested by the prompt and is one of the main purposes of the email.
出处: prbench:80e434dee8c7e108bfa66d32 | 话题: Family Law

## LEG-0686 [必须]
判据: The model compares trade in the EU internal market to other international markets, such as the USA.
提示: It is crucial for the model to include this, as it is central to the request of the prompt and thus will ensure that it is relevant and valuable to the user. This would ensure a factually relevant answer.
出处: prbench:82f6f5d97df37f3cbc5ba614 | 话题: International Law & Trade

## LEG-0687 [必须]
判据: The model explains the EU internal market using plain language.
提示: The model should answer using simplified legal terminology as it can be inferred from the prompt that the user is not an expert.
出处: prbench:82f6f5d97df37f3cbc5ba614 | 话题: International Law & Trade

## LEG-0688 [必须]
判据: The response references at least one precedent case or administrative ruling (e.g., Stone/Linx or BACEN authorization rulings) to illustrate regulator behavior.
提示: Requires concrete example integration into analysis.
出处: prbench:8c79f9f6bfc63d52574d5b1f | 话题: Regulatory & Administrative Law

## LEG-0689 [建议]
判据: The response is written in a warm tone typical of colleagues who work for the same business (e.g., use of inclusive pronouns like 'we,' friendly salutations and conversational phrases).
提示: The response should be formal yet warm as this is an internal advice note
出处: prbench:8eeebd5d4515765d5760a4ae | 话题: Real Estate & Property Law

## LEG-0690 [建议]
判据: The response acknowledges the struggles that the Underwriting Team have had in dealing with questions on estate rentcharges from conveyancers.
提示: People want to feel that their struggles are understood
出处: prbench:8eeebd5d4515765d5760a4ae | 话题: Real Estate & Property Law

## LEG-0691 [必须]
判据: The response includes a draft memo to colleagues.
提示: This was a request in the prompt
出处: prbench:8eeebd5d4515765d5760a4ae | 话题: Real Estate & Property Law

## LEG-0692 [必须]
判据: The draft memo to colleagues mentions that there have been struggles that the Underwriting Team have had in dealing with questions on estate rentcharges from conveyancers.
提示: People want to feel that their struggles are understood and if they feel understood they are more likely to take action
出处: prbench:8eeebd5d4515765d5760a4ae | 话题: Real Estate & Property Law

## LEG-0693 [必须]
判据: The draft memo is no longer than three paragraphs to ensure it can be consumed as an email.
提示: Colleagues are unlikely to digest a memo that is too long
出处: prbench:8eeebd5d4515765d5760a4ae | 话题: Real Estate & Property Law

## LEG-0694 [必须]
判据: Response provides the penalties that individual executives face (e.g., personal fines, potential prison sentences).
提示: warning about personal liability that is essential for a decision-maker to understand
出处: prbench:9168d6ebc668ee8ea121a9ae | 话题: Regulatory & Administrative Law

## LEG-0695 [必须]
判据: The response refers to arbitration proceedings initiated under the ICC Rules in Singapore.
提示: Essential.
出处: prbench:941f6cfdb5cb7387bf2f86d5 | 话题: Litigation & Dispute Resolution

## LEG-0696 [必须]
判据: The response provides a legal opinion addressing the specific asks as discrete sections (enforcement of the arbitration clause vis-à-vis public policy; jurisdictional conflict with electricity regulators; application of the New York Convention and Indian arbitration law; recommended dispute resolution and enforcement strategy).
提示: express demand of the prompt
出处: prbench:941f6cfdb5cb7387bf2f86d5 | 话题: Litigation & Dispute Resolution

## LEG-0697 [负面]
判据: The response includes extraneous legal case citations (e.g., Reilly, Donelson, Lane).
提示: Introduces unnecessary legal jargon when the user requested a direct, factual checklist.
出处: prbench:956143f4cd5b87f2fc736dfb | 话题: Constitutional & Civil Rights Law

## LEG-0698 [必须]
判据: The response references at least one enforcement action by CGU or CADE illustrating corporate liability for third-party misconduct.
提示: Requires the model to retrieve or recall a concrete enforcement case showing how regulators applied the anticorruption framework
出处: prbench:967ddb8fc1fb63452f55fc37 | 话题: Legal Ethics, Compliance & Risk Management

## LEG-0699 [必须]
判据: The model answers using a legal brief structure (including the elements for the statutory and common law test for reasonable force, analysis on the impact of an honest but mistaken belief in the need for force, and reference to case law).
提示: express request of the prompt
出处: prbench:98b5fc3f24d17fbffbc657d6 | 话题: Criminal Law

## LEG-0700 [必须]
判据: The model explains diminished responsibility using plain language.
提示: The model must answer using simplified language as it can be inferred that the user is not an expert.
出处: prbench:a16c66aeee819ae2b6e4d896 | 话题: Criminal Law

## LEG-0701 [必须]
判据: The response explicitly addresses the user's concern about circumvention, explaining that employers remain liable under California law for discriminatory effects of AI/automated tools, including internal systems and vendors.
提示: Implied by the question in the prompt.
出处: prbench:a6032058b3daee726134a8b6 | 话题: Labor & Employment Law

## LEG-0702 [建议]
判据: The response clearly provides a strategic recommendation for the "one more major filing," specifying the recommended jurisdiction (US or UK).
提示: answering the specific prompt
出处: prbench:ae41ba886e19c26d6e9a6ee2 | 话题: Intellectual Property (IP) Law

## LEG-0703 [必须]
判据: The response references at least one Brazilian court decision or regulatory precedent related to mergers.
提示: Precedents in this field are niche and rarely appear in AI-generated responses.
出处: prbench:b0684b149865f74f4c876603 | 话题: Corporate & Transactional Law

## LEG-0704 [建议]
判据: The response compares mergers with incorporation and spin-off, highlighting trade-offs.
提示: Forces comparative analysis instead of a one-dimensional answer.
出处: prbench:b0684b149865f74f4c876603 | 话题: Corporate & Transactional Law

## LEG-0705 [必须]
判据: The response cites at least one Brazilian precedent or case relevant to enforcement or dissolution of joint ventures.
提示: Very important because precedents in JV context are niche and models rarely bring them up.
出处: prbench:b67b684930564c8f40471846 | 话题: Corporate & Transactional Law

## LEG-0706 [必须]
判据: The response references at least one CADE decision involving joint ventures to illustrate how competition law may affect veto rights, exclusivity, or governance clauses.
提示: Very important, since it requires knowledge of CADE jurisprudence (antitrust authority in Brazil), which is not typically covered in standard corporate law overviews.
出处: prbench:b67b684930564c8f40471846 | 话题: Corporate & Transactional Law

## LEG-0707 [必须]
判据: The response includes the requested legal document, i.e., a legal memorandum.
提示: Explicit request of the user.
出处: prbench:bf46c6b357f81cd97cf5bf2d | 话题: Regulatory & Administrative Law

## LEG-0708 [建议]
判据: The response adheres to the requested legal document word count, i.e., 750 words.
提示: A request of the user which must be followed , but not of utmost importance.
出处: prbench:bf46c6b357f81cd97cf5bf2d | 话题: Regulatory & Administrative Law

## LEG-0709 [必须]
判据: The model explains all legal terms, other than summary judgment, that it refers to (e.g., strike out, costs, application, claim, real prospect of success) in simple English.
提示: Penalises the model for not reacting to a non-expert prompt
出处: prbench:c6910cdf68be125db3b808e0 | 话题: Litigation & Dispute Resolution

## LEG-0710 [必须]
判据: The model explains necessary legal terms (e.g., 'free movement of goods,' 'harmonisation') in non-technical language that is accessible to a business owner.
提示: The model answers using simplified legal concepts as it can be inferred from the prompt that the user is not an expert.
出处: prbench:ccf67eeff8beff07152565b7 | 话题: International Law & Trade

## LEG-0711 [必须]
判据: The response includes the English translations of Portuguese legal terms at least on first use (e.g. mandado de segurança, which means "Writ of Security").
提示: This helps to enusre clarity and understanding.
出处: prbench:d2bc628da42129c63871c387 | 话题: Regulatory & Administrative Law

## LEG-0712 [负面]
判据: The response includes a Portuguese legal term such as "mandado de segurança," without stating its English translation.
提示: It is important that un-English terms be translated to English to the user who asked their question in English.
出处: prbench:d2bc628da42129c63871c387 | 话题: Regulatory & Administrative Law

## LEG-0713 [必须]
判据: The response includes references to regional M&A precedents (such as LATAM-Delta or Bayer-Monsanto) in emphasizing the importance of coordination between national authorities.
提示: follows the instruction of referencing M&A precedents
出处: prbench:d56c7d425fbf8763b99f1c6f | 话题: Corporate & Transactional Law

## LEG-0714 [负面]
判据: The response includes verbatim the text of at least one of the eleven rotating text-only warnings currently required on cigarette packages (e.g., “SURGEON GENERAL’S WARNING: Cigarette Smoke Contains Carbon Monoxide”).
提示: counter to ask
出处: prbench:d78b6d546b7cc9fff2113f65 | 话题: Regulatory & Administrative Law

## LEG-0715 [必须]
判据: The model answers in simple language.
提示: The model should answer using simple language as it can be inferred from the prompt that the user is not an expert.
出处: prbench:dbb6c3182311826740228c97 | 话题: International Law & Trade

## LEG-0716 [必须]
判据: Adding this in here, this task is all just spam and AI slop.
提示: this whole task is moot, too much to change
出处: prbench:dbb6c3182311826740228c97 | 话题: International Law & Trade

## LEG-0717 [必须]
判据: The model answers using simplified legal concepts.
提示: The model should simplify complex legal concepts as it can be inferred from the prompt that the user is not an expert.
出处: prbench:dbb6c3182311826740228c97 | 话题: International Law & Trade

## LEG-0718 [负面]
判据: The response contains excessive statutory or article citations that are redundant or unnecessary for understanding, for example, repeating multiple LPAF and constitutional articles in sequence.
提示: The response overuses legal references without improving clarity, making it less usable for a non-expert reader.
出处: prbench:e169edb629ce3688e1aa1a6e | 话题: Regulatory & Administrative Law

## LEG-0719 [负面]
判据: The response cites article-level provisions from a specific ANTT resolution, for example “Resolution 5.083/2016, art. 26, §1º, II.”
提示: The response introduces brittle, version-specific pinpoint citations that are prone to inaccuracy across programs and updates, reducing reliability for a non-expert reader.
出处: prbench:e169edb629ce3688e1aa1a6e | 话题: Regulatory & Administrative Law

## LEG-0720 [负面]
判据: The response mentions specific docket or case numbers, for example, “REsp 1.834.567/RS.”
提示: The response omits a general, accurate explanation of the relevant legal principle.
出处: prbench:e169edb629ce3688e1aa1a6e | 话题: Regulatory & Administrative Law

## LEG-0721 [负面]
判据: Includes overly generic language.
提示: Indicates lack of depth, contrary to the prompts requirements.
出处: prbench:e2a9a9666d1eec1b8a268e1e | 话题: Corporate & Transactional Law

## LEG-0722 [负面]
判据: Includes a disproportionate emphasis on general principles (e.g., freedom of contract).
提示: Distracts from the goal of providing strategic client-focused analysis.
出处: prbench:e2a9a9666d1eec1b8a268e1e | 话题: Corporate & Transactional Law

## LEG-0723 [负面]
判据: The response presents more than 600 words.
提示: Dense texts could be boring for lay person.
出处: prbench:e75bec55f1d72f6fee867fb0 | 话题: Labor & Employment Law

## LEG-0724 [必须]
判据: The response states that it is a draft white paper on legal taxation issues of hybrid work arrangements.
提示: This criterion responds directly to the prompt's request for legal taxation issues of hybrid work arrangements.
出处: prbench:e8503e7da631a63b0ab52582 | 话题: Taxation & Cross-Border Structuring

## LEG-0725 [必须]
判据: The response states that it is a draft white paper on legal taxation issues of employer-employee relationships that cross state borders.
提示: This criterion responds directly to the prompt's request for legal taxation issues of employer-employee relationships that cross state borders.
出处: prbench:e8503e7da631a63b0ab52582 | 话题: Taxation & Cross-Border Structuring

## LEG-0726 [必须]
判据: The response states that it is a draft white paper on legal taxation issues of remote work arrangements.
提示: This criterion responds directly to the prompt's request for legal taxation issues of remote work arrangements.
出处: prbench:e8503e7da631a63b0ab52582 | 话题: Taxation & Cross-Border Structuring

## LEG-0727 [建议]
判据: The response presents each memo heading in bold text for emphasis.
提示: This helps for clarity and emphasis on important details in the memo.
出处: prbench:e883be100346682cf86edde7 | 话题: Regulatory & Administrative Law

## LEG-0728 [必须]
判据: The response presents its analysis in a legal memorandum.
提示: The user explicitly requests a legal memo.
出处: prbench:e883be100346682cf86edde7 | 话题: Regulatory & Administrative Law

## LEG-0729 [建议]
判据: Provides its information in not more than 750 words.
提示: This is an explicit request, but not that important.
出处: prbench:e883be100346682cf86edde7 | 话题: Regulatory & Administrative Law

## LEG-0730 [必须]
判据: The response notes that the end of Q3 is in two days.
提示: This serves as a reminder to the user and also as a basis for establishing when the plan is implemented.
出处: prbench:ee98ca98d0eb661ea16a266e | 话题: Corporate & Transactional Law

## LEG-0731 [负面]
判据: The response contains an unnecessary introduction (e.g. "of course", "sure", "excellent question", "short answer").
提示: Does not add any information to response.
出处: prbench:eff765cbb55ed1e2f857f760 | 话题: Taxation & Cross-Border Structuring

## LEG-0732 [负面]
判据: The response includes Portuguese legal terms, for example, "seguro-garantia".
提示: Mixing languages reduces accessibility for English readers.
出处: prbench:effcf67e5b1207bb76a85e5f | 话题: Litigation & Dispute Resolution

## LEG-0733 [必须]
判据: The response must not mention Scotland, Wales, and Northern Ireland.
提示: This is because the user prompt mentioned England and not the UK.
出处: prbench:f12c213a3b8928768674ad2c | 话题: Real Estate & Property Law

## LEG-0734 [必须]
判据: The response includes a summary table comparing deposit and Reposit.
提示: This is important so that the user can see the requested information at a glance.
出处: prbench:f12c213a3b8928768674ad2c | 话题: Real Estate & Property Law

## LEG-0735 [建议]
判据: The response should be presented in bullet points.
提示: This is to ensure that the information in the response are clearly presented and readable.
出处: prbench:f12c213a3b8928768674ad2c | 话题: Real Estate & Property Law

## LEG-0736 [负面]
判据: The response is more than 300 words long.
提示: This is important to ensure that the response is not verbose and does not include irrelevant information.
出处: prbench:f12c213a3b8928768674ad2c | 话题: Real Estate & Property Law

## LEG-0737 [负面]
判据: The response includes speculative practical advice (e.g., "consult your lawyer immediately", "budget for costs") that shifts away from the legal application question.
提示: Dilutes focus by moving outside the prompts legal scope.
出处: prbench:f2febac7e5a617057be85f6f | 话题: Litigation & Dispute Resolution

## LEG-0738 [建议]
判据: The response cites Ford v. Schering-Plough (3d Cir. 1998), for example, “Ford v. Schering-Plough Corp., 145 F.3d 601, 612–14 (3d Cir. 1998).”
提示: Ensures reliance on controlling Third Circuit precedent.
出处: prbench:f560b62ec275f75ec71ef8bf | 话题: Constitutional & Civil Rights Law

## LEG-0739 [必须]
判据: The response's one-page executive summary mentions Section 301 duties by name.
提示: The prompt requested the one-pager.
出处: prbench:f5f57bd93d6c87b01d64ffc2 | 话题: International Law & Trade

## LEG-0740 [必须]
判据: The response identifies special tariffs (such as Section 301 tariffs) first in the prioritized risk assessment.
提示: The 301 risks are more significant than the classification risks.
出处: prbench:f5f57bd93d6c87b01d64ffc2 | 话题: International Law & Trade

## LEG-0741 [建议]
判据: The response includes a sensitivity analysis showing a 0% duty under an HTSUS classification under heading 8517.
提示: The prompt requested sensitivity analysis.
出处: prbench:f5f57bd93d6c87b01d64ffc2 | 话题: International Law & Trade

## LEG-0742 [负面]
判据: The response identifies AD/CVD as a potential risk.
提示: None of the AD/CVD orders apply to the product.
出处: prbench:f5f57bd93d6c87b01d64ffc2 | 话题: International Law & Trade

## LEG-0743 [必须]
判据: The response presents a side-by-side table with these five labeled columns: (1) Price/Consideration, (2) Sale Type (asset vs stock), (3) Expected Tax Character, (4) Seller Involvement/Term, (5) Risk/Liability Retained.
提示: Makes “side-by-side” objective and uniformly gradable.
出处: prbench:f73e2d130068ee4d87eca6b8 | 话题: Taxation & Cross-Border Structuring

## LEG-0744 [必须]
判据: The response states that the $700,000 revenue-based earn-out is not tied to profits but to revenue only.
提示: Prevents confusion between profit-sharing and revenue-based payments.
出处: prbench:f73e2d130068ee4d87eca6b8 | 话题: Taxation & Cross-Border Structuring

## LEG-0745 [必须]
判据: The model answers using simple language.
提示: The model should answer using simplified language as it can be inferred that the user is not an expert.
出处: prbench:f7c16fffbe08be27e655f575 | 话题: Criminal Law

## LEG-0746 [负面]
判据: The response includes an unnecessary pleasantry (e.g., "of course").
提示: Is unnecessary to the user.
出处: prbench:fb6f178db4eec6b5980c10d3 | 话题: Litigation & Dispute Resolution

## LEG-0747 [必须]
判据: Response has a summary section at the end that lists PCT's impact on harmonization for patent filings internationally.
提示: Conforms with professional writing standards.
出处: prbench:fd5b7328f6f4c591ccd7f6b1 | 话题: Intellectual Property (IP) Law

