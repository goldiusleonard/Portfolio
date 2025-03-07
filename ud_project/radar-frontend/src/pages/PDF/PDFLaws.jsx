import React from "react";

const PDFLaws = () => {
  const sections = [
    {
      category: "Law Violations",
      items: [
        {
          law: "AKTA Hasutan",
          details: [
            "Section Violated: Section 3(1)(e), Section 4",
            "Violation Analysis: The content shows a tendency to promote feelings of ill-will and hostility, which is considered a seditious tendency under Section 3(1)(e). Furthermore, uttering seditious words is a violation of Section 4.",
          ],
        },
        {
          law: "PENAL CODE",
          details: [
            "Section Violated: Section 298A",
            "Violation Analysis: The offensive remarks against a specific individual could be interpreted as actions likely to cause disharmony or feelings of enmity, hatred, or ill-will on religious grounds, thus violating Section 298A.",
          ],
        },
        {
          law: "CMA 1998",
          details: [
            "Section Violated: Section 233(1)(a)",
            "Violation Analysis: The individual knowingly made, created, or solicited offensive remarks and initiated transmission via a network service with intent to harass another person, violating Section 233(1)(a).",
          ],
        },
        {
          law: "TikTok Guidelines",
          details: [
            "Section Violated: Hate Speech and Hateful Behavior, Harassment and Bullying",
            "Violation Analysis: The video contains personal attacks and derogatory comments which violate TikTok's guidelines against hate speech, hateful behavior, and harassment.",
          ],
        },
      ],
    },
    {
      category: "Internet Violations",
      items: [
        {
          law: "AKTA Hasutan",
          details: [
            "Section Violated: Section 3(1)(e), Section 4",
            "Violation Analysis: The content shows a tendency to promote feelings of ill-will and hostility, which is considered a seditious tendency under Section 3(1)(e). Furthermore, uttering seditious words is a violation of Section 4.",
          ],
        },
        {
          law: "PENAL CODE",
          details: [
            "Section Violated: Section 298A",
            "Violation Analysis: The offensive remarks against a specific individual could be interpreted as actions likely to cause disharmony or feelings of enmity, hatred, or ill-will on religious grounds, thus violating Section 298A.",
          ],
        },
        {
          law: "CMA 1998",
          details: [
            "Section Violated: Section 233(1)(a)",
            "Violation Analysis: The individual knowingly made, created, or solicited offensive remarks and initiated transmission via a network service with intent to harass another person, violating Section 233(1)(a).",
          ],
        },
        {
          law: "TikTok Guidelines",
          details: [
            "Section Violated: Hate Speech and Hateful Behavior, Harassment and Bullying",
            "Violation Analysis: The video contains personal attacks and derogatory comments which violate TikTok's guidelines against hate speech, hateful behavior, and harassment.",
          ],
        },
      ],
    },
    {
      category: "Internet Violations",
      items: [
        {
          law: "AKTA Hasutan",
          details: [
            "Section Violated: Section 3(1)(e), Section 4",
            "Violation Analysis: The content shows a tendency to promote feelings of ill-will and hostility, which is considered a seditious tendency under Section 3(1)(e). Furthermore, uttering seditious words is a violation of Section 4.",
          ],
        },
        {
          law: "PENAL CODE",
          details: [
            "Section Violated: Section 298A",
            "Violation Analysis: The offensive remarks against a specific individual could be interpreted as actions likely to cause disharmony or feelings of enmity, hatred, or ill-will on religious grounds, thus violating Section 298A.",
          ],
        },
        {
          law: "CMA 1998",
          details: [
            "Section Violated: Section 233(1)(a)",
            "Violation Analysis: The individual knowingly made, created, or solicited offensive remarks and initiated transmission via a network service with intent to harass another person, violating Section 233(1)(a).",
          ],
        },
        {
          law: "TikTok Guidelines",
          details: [
            "Section Violated: Hate Speech and Hateful Behavior, Harassment and Bullying",
            "Violation Analysis: The video contains personal attacks and derogatory comments which violate TikTok's guidelines against hate speech, hateful behavior, and harassment.",
          ],
        },
      ],
    },
    {
      category: "Law Violations",
      items: [
        {
          law: "AKTA Hasutan",
          details: [
            "Section Violated: Section 3(1)(e), Section 4",
            "Violation Analysis: The content shows a tendency to promote feelings of ill-will and hostility, which is considered a seditious tendency under Section 3(1)(e). Furthermore, uttering seditious words is a violation of Section 4.",
          ],
        },
        {
          law: "PENAL CODE",
          details: [
            "Section Violated: Section 298A",
            "Violation Analysis: The offensive remarks against a specific individual could be interpreted as actions likely to cause disharmony or feelings of enmity, hatred, or ill-will on religious grounds, thus violating Section 298A.",
          ],
        },
        {
          law: "CMA 1998",
          details: [
            "Section Violated: Section 233(1)(a)",
            "Violation Analysis: The individual knowingly made, created, or solicited offensive remarks and initiated transmission via a network service with intent to harass another person, violating Section 233(1)(a).",
          ],
        },
        {
          law: "TikTok Guidelines",
          details: [
            "Section Violated: Hate Speech and Hateful Behavior, Harassment and Bullying",
            "Violation Analysis: The video contains personal attacks and derogatory comments which violate TikTok's guidelines against hate speech, hateful behavior, and harassment.",
          ],
        },
      ],
    },
    {
      category: "Internet Violations",
      items: [
        {
          law: "AKTA Hasutan",
          details: [
            "Section Violated: Section 3(1)(e), Section 4",
            "Violation Analysis: The content shows a tendency to promote feelings of ill-will and hostility, which is considered a seditious tendency under Section 3(1)(e). Furthermore, uttering seditious words is a violation of Section 4.",
          ],
        },
        {
          law: "PENAL CODE",
          details: [
            "Section Violated: Section 298A",
            "Violation Analysis: The offensive remarks against a specific individual could be interpreted as actions likely to cause disharmony or feelings of enmity, hatred, or ill-will on religious grounds, thus violating Section 298A.",
          ],
        },
        {
          law: "CMA 1998",
          details: [
            "Section Violated: Section 233(1)(a)",
            "Violation Analysis: The individual knowingly made, created, or solicited offensive remarks and initiated transmission via a network service with intent to harass another person, violating Section 233(1)(a).",
          ],
        },
        {
          law: "TikTok Guidelines",
          details: [
            "Section Violated: Hate Speech and Hateful Behavior, Harassment and Bullying",
            "Violation Analysis: The video contains personal attacks and derogatory comments which violate TikTok's guidelines against hate speech, hateful behavior, and harassment.",
          ],
        },
      ],
    },
  ];

  return (
    <div className="pdf-law-container">
      <h1 className="pdf-law-title">Standards & Regulations</h1>
      <div className="pdf-law-contentCard">
        <h2 className="pdf-law-subTitle">Malaysia Good Content Terms</h2>
        <div className="pdf-law-section">
          {sections.map((section, i) => (
            <div key={i} className="pdf-law-sectionContent">
              <h3 className="pdf-law-sectionTitle">{section.category}</h3>
              <div className="pdf-law-divider">
                {section.items.map((item, j) => (
                  <div key={j} className="pdf-law-item">
                    <h4 className="pdf-law-itemTitle">{item.law}</h4>
                    <ul className="pdf-law-itemList">
                      {item.details.map((detail, k) => (
                        <li key={k} className="pdf-law-itemText">
                          {detail}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PDFLaws;
