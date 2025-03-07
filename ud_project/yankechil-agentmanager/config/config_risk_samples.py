risk_levels_general = {
    "High Risk": [
        "Promoting a fake gold investment scheme with forged certifications of authenticity lures victims into financial ruin, while spreading false information that a specific racial group is responsible for a surge in crime incites racial hatred and violence. Similarly, glorifying human trafficking as a lucrative opportunity on social media perpetuates exploitation, and encouraging violence against women by promoting domestic abuse as “discipline” poses a grave violation of human rights.",
    ],
    "Medium Risk": [
        "Exaggerating the profit potential of a cryptocurrency project without providing verified data or disclaimers misleads investors, just as making an insensitive joke about a religious practice perpetuates stereotypes unintentionally. Discussing unverified rumors about illegal immigrants exploiting social benefits adds to misinformation, while dismissive comments downplaying the importance of child labor laws as “overprotective” can trivialize serious issues.",
    ],
    "Low Risk": [
        "Discussing Forex investment options in a neutral and educational tone without promoting specific platforms informs potential investors without harm. Criticizing a royal policy decision in a non-inflammatory manner encourages constructive dialogue, while raising awareness about common job scams through general discussions promotes vigilance. Additionally, analyzing sexual crime statistics in a factual and neutral manner supports better understanding and policy-making without causing offense.",
    ],
}

risk_levels_sample = {
    "Scam": {
        "Gold": {
            "High Risk": [
                "Promoting fraudulent gold investment schemes, such as 'too good to be true' offers where individuals are encouraged to invest large sums of money in fake or non-existent gold assets.",
                "Spreading misinformation about gold prices or investments with the intent to deceive or defraud, such as claiming that gold prices will surge drastically without any basis or spreading fake news about market conditions.",
                "Targeting individuals with scams involving fake gold purchases or sales, where individuals are convinced to buy counterfeit gold or gold from unverified sources that they believe to be legitimate.",
            ],
            "Medium Risk": [
                "Sharing misleading or exaggerated claims about gold investment opportunities, such as inflating the potential returns on gold investments without supporting data or implying guaranteed profits.",
                "Making unverified statements about gold sources or quality, such as claiming a particular gold mine or investment product has a better quality or higher value than it truly does, without credible proof.",
            ],
            "Low Risk": [
                "Discussing gold-related investments in non-technical or speculative contexts, such as casual conversations about the future of gold in an uncertain market or speculative discussions on the potential of gold as a safe-haven investment.",
            ],
        },
        "Cryptocurrency": {
            "High Risk": [
                "Promoting fraudulent cryptocurrency schemes or Ponzi scams, such as investment platforms that promise guaranteed returns but ultimately defraud investors by using new investments to pay off earlier ones.",
                "Encouraging investment in fake cryptocurrencies or fraudulent exchanges that do not exist or are designed to steal investors' funds through misleading marketing or scams.",
                "Spreading misinformation about cryptocurrency markets with the intent to defraud, such as making false claims about the value of a cryptocurrency, its future potential, or its legitimacy to manipulate prices or mislead investors.",
            ],
            "Medium Risk": [
                "Overstating cryptocurrency potential or returns without evidence, such as claiming that a particular cryptocurrency will skyrocket in value without providing verifiable reasons or analysis to support the claim.",
                "Discussing unverified or speculative cryptocurrency investment opportunities, such as promoting lesser-known coins or tokens based on rumors or unproven data, which could lead investors to make uninformed decisions.",
            ],
            "Low Risk": [
                "Providing basic cryptocurrency information that may be incomplete but not harmful, such as explaining how cryptocurrencies work, their underlying technology (blockchain), or general information about the market, without giving specific investment advice.",
                "Discussing cryptocurrencies in an educational or neutral manner, providing information on their benefits, risks, or the overall market without making exaggerated claims or pushing specific investments.",
            ],
        },
        "Forex": {
            "High Risk": [
                "Promoting fraudulent Forex trading schemes, such as Ponzi schemes, pump-and-dump tactics, or any other investment opportunities that promise unrealistic returns with the intent to defraud individuals.",
                "Sharing fake or manipulated Forex market data with the purpose of misleading individuals into making trades, often to benefit the person sharing the data or cause harm to the trader.",
                "Encouraging the use of unverified or unregulated Forex platforms or brokers that lack transparency, proper licensing, or security, potentially leading to financial loss or fraud.",
            ],
            "Medium Risk": [
                "Offering questionable Forex trading advice or strategies without intent to defraud, such as promoting high-risk trades without proper risk management or sharing personal opinions without a solid financial basis.",
                "Discussing speculative Forex trading strategies or market predictions that are based on unverified information or personal guesses, which could mislead individuals into making poor financial decisions.",
            ],
            "Low Risk": [
                "Discussing Forex as an investment option in neutral or educational contexts, such as explaining how Forex trading works, potential risks, or the mechanics of currency exchange markets.",
                "Sharing general, factual information about Forex trading, such as the role of central banks, interest rates, or geopolitical events in influencing currency prices, without promoting specific trading platforms or financial gains.",
            ],
        },
    },
    "3R": {
        "Race": {
            "High Risk": [
                "Explicit Racial Slurs: Offensive or derogatory terms targeting an individual's race or ethnicity.",
                "Promoting Racial Violence: Inciting or endorsing violence or hate crimes based on race.",
                "Spreading Racially Motivated Misinformation: Disseminating false or harmful information to provoke racial hatred or discrimination.",
                "Threatening Racially Targeted Individuals: Making threats of harm or violence based on racial or ethnic background.",
                "Encouraging Racial Segregation or Discrimination: Advocating for policies or behaviors promoting racial segregation or systemic discrimination.",
            ],
            "Medium Risk": [
                "Mild Racial Insults: Hurtful but less severe derogatory or negative terms.",
                "Making Racially Insensitive Jokes: Sharing offensive or inappropriate jokes without intent to incite violence.",
                "Expressing Racial Bias: Sharing opinions or beliefs reflecting racial prejudices or stereotypes without direct threats or calls for violence.",
                "Discussing Racial Stereotypes: Commenting on or perpetuating harmful stereotypes without being overtly violent or threatening.",
            ],
            "Low Risk": [
                "Unintentional Racial Insensitivity: Comments or statements that may be racially insensitive or offensive but not intended to be harmful.",
                "Criticizing Racial Groups in Non-Derogatory Ways: Offering criticism or commentary on a racial group without intent to incite hatred or violence.",
                "Discussing Race in Neutral Contexts: Conversations about race or ethnicity that are informative and non-offensive.",
            ],
        },
        "Religion": {
            "High Risk": [
                "Explicit Religious Slurs: Offensive or derogatory terms targeting an individual's religion or beliefs.",
                "Promoting Religious Violence: Inciting or endorsing violence or hate crimes based on religion.",
                "Spreading Misinformation About Religions: Disseminating false or harmful information to provoke hatred or discrimination against a religion.",
                "Threatening Religious Figures or Followers: Making threats of harm or violence against religious leaders or followers based on their beliefs.",
                "Encouraging Religious Persecution: Advocating for actions or policies promoting religious persecution or systemic discrimination.",
            ],
            "Medium Risk": [
                "Mild Religious Insults: Hurtful but less severe derogatory or negative terms.",
                "Making Religiously Insensitive Jokes: Sharing offensive or inappropriate jokes about religious beliefs.",
                "Expressing Religious Bias: Sharing opinions or beliefs reflecting religious prejudices or stereotypes without direct threats or calls for violence.",
                "Discussing Religious Stereotypes: Commenting on or perpetuating harmful stereotypes about a religion without being overtly violent or threatening.",
            ],
            "Low Risk": [
                "Unintentional Religious Insensitivity: Comments or statements that may be religiously insensitive or offensive but not intended to cause harm.",
                "Criticizing Religious Practices in Non-Derogatory Ways: Offering criticism or commentary on religious practices without intent to incite hatred or violence.",
                "Discussing Religion in Neutral Contexts: Conversations about religion that are factual, informative, and non-offensive.",
            ],
        },
        "Royalty": {
            "High Risk": [
                "Explicit Royal Insults: Highly offensive or derogatory terms targeting members of a royal family or monarchy.",
                "Promoting Violence Against Royals: Inciting or endorsing violence or harm against members of a royal family or monarchy.",
                "Spreading Misinformation About Royals: Disseminating false or harmful information to provoke hatred or violence against royalty.",
                "Threatening Royals: Making direct threats of harm or violence towards members of a royal family.",
                "Encouraging Disregard for Royal Authority: Advocating for actions or behaviors that seek to undermine or overthrow the monarchy in a harmful or violent manner.",
            ],
            "Medium Risk": [
                "Mild Royal Insults: Hurtful but less severe negative or derogatory language.",
                "Making Inappropriate Jokes About Royals: Sharing offensive or inappropriate jokes about members of the royal family.",
                "Expressing Bias Against Royals: Sharing opinions or beliefs reflecting negative stereotypes or prejudices about royalty without direct threats.",
                "Discussing Royal Controversies: Commenting on or perpetuating provocative but not overtly harmful controversies involving royalty.",
            ],
            "Low Risk": [
                "Unintentional Insensitivity Towards Royals: Comments or statements that may be insensitive or critical of royalty but are not meant to be harmful.",
                "Criticizing Royal Practices in Non-Derogatory Ways: Offering criticism or commentary on royal practices or decisions without intent to incite hatred or violence.",
                "Discussing Royals in Neutral Contexts: Conversations about the royal family or monarchy that are factual, informative, and non-offensive.",
            ],
        },
    },
    "ATIPSOM": {
        "Human Trafficking": {
            "High Risk": [
                "Promoting or glorifying human trafficking activities, such as sharing content that praises or encourages trafficking for forced labor, sexual exploitation, or other illegal purposes.",
                "Sharing detailed information about trafficking routes, methods, or networks, including maps, contacts, or strategies that enable illegal transport of individuals.",
                "Disseminating content encouraging the exploitation of trafficked individuals, such as advertising illegal services, forced labor, or involvement in exploitative activities.",
            ],
            "Medium Risk": [
                "Making insensitive or dismissive comments about human trafficking victims, such as statements that blame victims for their situation or trivialize the severity of their experiences.",
                "Sharing unverified or speculative claims about human trafficking incidents, routes, or networks, which may contribute to misinformation, fear-mongering, or misdirection of resources.",
                "Using ambiguous or misleading language that could unintentionally normalize or minimize the issue of trafficking, such as joking about trafficking-related topics.",
            ],
            "Low Risk": [
                "Discussing human trafficking in a neutral, educational, or informative context, such as raising awareness about its causes, consequences, or preventative measures.",
                "Sharing factual, verified information about human trafficking incidents, statistics, laws, or survivor stories, with appropriate sensitivity and consent where required.",
                "Engaging in academic, policy, or awareness-based discussions to highlight the realities of trafficking and promote efforts to combat exploitation.",
            ],
        },
        "Job Scam": {
            "High Risk": [
                "Advertising fraudulent job opportunities with the intent to exploit individuals, such as promoting fake roles that require upfront payments or personal information.",
                "Spreading deliberate misinformation about job requirements, such as false promises of high salaries, benefits, or remote opportunities to lure individuals into scams.",
                "Encouraging individuals to pay fees, provide bank details, or submit personal documents for fake job offers under the pretense of securing employment.",
            ],
            "Medium Risk": [
                "Sharing speculative or unverified job opportunities, such as posting roles without verifying their authenticity or reliability, which may inadvertently mislead job seekers.",
                "Misrepresenting job benefits, requirements, or working conditions without malicious intent, such as exaggerating pay, benefits, or job security to attract candidates.",
                "Discussing ambiguous or vague job offers where the legitimacy of the opportunity cannot be confirmed but without clear intent to exploit.",
            ],
            "Low Risk": [
                "Discussing job scams in general terms, such as sharing warnings, educational content, or advice about identifying and avoiding fraudulent job opportunities.",
                "Raising awareness about common job scam tactics, such as fake interviews, upfront fees, or promises of guaranteed employment.",
                "Providing factual or verified information about job markets, recruitment processes, or common red flags in employment offers.",
            ],
        },
        "Illegal Immigrants": {
            "High Risk": [
                "Promoting exploitation or abuse of illegal immigrants, such as encouraging forced labor, unsafe living conditions, or other forms of mistreatment.",
                "Encouraging or facilitating the smuggling, harboring, or illegal transport of undocumented individuals across borders, including sharing methods, contacts, or networks.",
                "Spreading hate speech targeting illegal immigrants, such as using dehumanizing language, inciting violence, or promoting discrimination against undocumented individuals or communities.",
            ],
            "Medium Risk": [
                "Making insensitive or dismissive comments about illegal immigrants, such as statements that trivialize their struggles or blame them unfairly for broader social or economic issues.",
                "Discussing stereotypes or prejudices about illegal immigrants, such as generalizing them as criminals, job stealers, or burdens without factual evidence or context.",
                "Sharing unverified claims or misinformation about illegal immigrants, such as exaggerated numbers or false accusations of wrongdoing.",
            ],
            "Low Risk": [
                "Discussing immigration issues in neutral or non-derogatory contexts, such as analyzing policies, economic impacts, or humanitarian concerns without promoting bias.",
                "Sharing factual or verified information about immigration processes, challenges faced by undocumented individuals, or legal frameworks related to immigration.",
                "Engaging in discussions that highlight solutions or raise awareness about the complexities of illegal immigration, such as addressing root causes or sharing support initiatives.",
            ],
        },
        "Sexual and Family": {
            "Sexual Crimes (porn, rape)": {
                "High Risk": [
                    "Sharing or promoting explicit sexual content involving exploitation, such as non-consensual pornography, child sexual abuse material, or content that glorifies sexual crimes.",
                    "Advocating for or endorsing sexual violence or crimes, including statements that justify rape, harassment, or other forms of sexual exploitation.",
                    "Disseminating harmful stereotypes or victim-blaming narratives about individuals affected by sexual crimes, such as suggesting victims are responsible for the crime.",
                ],
                "Medium Risk": [
                    "Making insensitive jokes or comments about sexual crimes, such as trivializing rape, assault, or exploitation through humor or dismissive language.",
                    "Discussing stereotypes or generalizations about victims or perpetrators of sexual crimes without malicious intent but in ways that may perpetuate stigma or bias.",
                    "Sharing unverified claims or speculative information about sexual crimes, which could spread misinformation or mislead audiences.",
                ],
                "Low Risk": [
                    "Discussing sexual crimes in neutral or informative contexts, such as raising awareness about the impacts of sexual violence, survivor stories, or preventive measures.",
                    "Sharing factual and verified information about laws, policies, or societal responses to sexual crimes in a respectful and sensitive manner.",
                    "Analyzing the causes, consequences, and solutions to address sexual violence and exploitation, such as discussions on education, support systems, or legal frameworks.",
                ],
            },
        },
        "Violation of Women's Rights": {
            "High Risk": [
                "Advocating for suppression or violence against women, such as promoting physical harm, domestic violence, or denial of basic rights like education, voting, or employment.",
                "Encouraging systemic discrimination against women, including support for laws, policies, or practices that oppress or restrict women's freedom and opportunities.",
                "Spreading harmful stereotypes or narratives to justify violations of women's rights, such as portraying women as inferior, incapable, or deserving of mistreatment.",
            ],
            "Medium Risk": [
                "Making insensitive or dismissive comments about women's rights issues, such as trivializing struggles for equality or belittling the significance of gender-based challenges.",
                "Criticizing women's rights movements in a non-malicious way, such as questioning their goals, methods, or impact without actively promoting harm or discrimination.",
                "Sharing unverified or speculative claims about women's rights violations or movements, which may unintentionally contribute to misinformation or confusion.",
            ],
            "Low Risk": [
                "Discussing women's rights in neutral, factual, or educational contexts, such as analyzing gender equality policies, historical struggles, or ongoing challenges faced by women.",
                "Raising awareness about violations of women's rights, including issues like unequal pay, gender-based violence, or lack of access to healthcare and education.",
                "Highlighting solutions and positive steps toward achieving gender equality, such as promoting women's empowerment initiatives, legal reforms, or cultural change.",
            ],
        },
        "Violation of Children's Rights": {
            "High Risk": [
                "Promoting or endorsing child abuse, exploitation, or violence, such as encouraging physical harm, neglect, trafficking, or sexual exploitation of children.",
                "Disseminating harmful stereotypes to justify violations of children's rights, such as claiming that children do not require education or protection from labor.",
                "Sharing content that glorifies or normalizes exploitative practices like child labor, child marriages, or any form of abuse, portraying them as acceptable or beneficial.",
            ],
            "Medium Risk": [
                "Making insensitive or dismissive comments about children's rights issues, such as trivializing the importance of child protection laws or dismissing cases of abuse or neglect.",
                "Criticizing children's advocacy movements in a non-malicious way, such as questioning their methods, effectiveness, or necessity without endorsing harm.",
                "Sharing unverified or speculative claims about violations of children's rights, which could spread misinformation or downplay serious issues.",
            ],
            "Low Risk": [
                "Discussing children's rights in neutral, factual, or educational contexts, such as analyzing policies, historical challenges, or global efforts to protect children.",
                "Raising awareness about violations of children's rights, including issues like child abuse, trafficking, labor, or denial of education and healthcare.",
                "Highlighting solutions or initiatives aimed at protecting and promoting children's rights, such as legal reforms, child protection programs, or educational campaigns.",
            ],
        },
    },
}
