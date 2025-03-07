export const currentPredictionOptions = [
  "Current",
  "Prediction"
]

export const riskOptions = [
  "Risk",
  "Engagement"
]

export const monthsOptions = [
  "1 Month",
  "3 Month",
  "6 Month"
]

export const categoryDetails = [
  {
    category: "Scam",
    totalSubCategory: 3,
    totalTopics: 26,
    aboutCategory:
      "Internet scams are online deceptions designed to trick people into giving away personal information or money. Common types include phishing emails, fake online stores, and fraudulent investment opportunities.",
    sentiment: "negative",
    risk: {
      high: 50,
      medium: 30,
      low: 20,
    },
  },
  {
    category: "Hate Speech",
    totalSubCategory: 5,
    totalTopics: 40,
    aboutCategory:
      "Hate speech refers to content that promotes hatred or violence against individuals or groups based on attributes like race, religion, gender, or sexual orientation. This can include slurs, offensive memes, and calls for violence.",
    sentiment: "negative",
    risk: {
      high: 60,
      medium: 30,
      low: 10,
    },
  },
  {
    category: "Misinformation",
    totalSubCategory: 4,
    totalTopics: 35,
    aboutCategory:
      "Misinformation is the spread of false or misleading information. It often includes fake news articles, manipulated images, and conspiracy theories that can influence public opinion or incite panic.",
    sentiment: "negative",
    risk: {
      high: 40,
      medium: 35,
      low: 25,
    },
  },
  {
    category: "Cyberbullying",
    totalSubCategory: 6,
    totalTopics: 30,
    aboutCategory:
      "Cyberbullying involves harassment, threats, or humiliation directed at individuals online. Common forms include posting offensive comments, sharing embarrassing content, or spreading rumors via social media platforms.",
    sentiment: "negative",
    risk: {
      high: 50,
      medium: 40,
      low: 10,
    },
  },
  {
    category: "Violence/Graphic",
    totalSubCategory: 3,
    totalTopics: 20,
    aboutCategory:
      "Violence or graphic content includes depictions of extreme physical harm, gore, or violent acts. These can be unsettling and are often inappropriate for most audiences.",
    sentiment: "negative",
    risk: {
      high: 70,
      medium: 20,
      low: 10,
    },
  },
  {
    category: "Explicit Content",
    totalSubCategory: 4,
    totalTopics: 25,
    aboutCategory:
      "Explicit content includes materials of a sexual nature or images and videos that are inappropriate for general audiences. Examples include adult material or explicit language.",
    sentiment: "negative",
    risk: {
      high: 40,
      medium: 40,
      low: 20,
    },
  },
  {
    category: "Copyright Infringement",
    totalSubCategory: 3,
    totalTopics: 18,
    aboutCategory:
      "Copyright infringement refers to unauthorized use or reproduction of copyrighted material such as music, videos, images, or written works without proper attribution or permissions.",
    sentiment: "negative",
    risk: {
      high: 30,
      medium: 50,
      low: 20,
    },
  },
  {
    category: "Privacy Violations",
    totalSubCategory: 4,
    totalTopics: 22,
    aboutCategory:
      "Privacy violations occur when personal information, such as addresses, contact details, or private images, is shared without consent. This can lead to harm or harassment.",
    sentiment: "negative",
    risk: {
      high: 40,
      medium: 40,
      low: 20,
    },
  },
  {
    category: "Cyber Threats",
    totalSubCategory: 5,
    totalTopics: 30,
    aboutCategory:
      "Cyber threats include activities aimed at disrupting, damaging, or gaining unauthorized access to computer systems. Examples include hacking, malware attacks, and phishing scams.",
    sentiment: "negative",
    risk: {
      high: 60,
      medium: 30,
      low: 10,
    },
  },
  {
    category: "Regulatory Violations",
    totalSubCategory: 2,
    totalTopics: 15,
    aboutCategory:
      "Regulatory violations involve actions that breach legal or industry standards, such as publishing restricted content or failing to adhere to compliance rules set by governing bodies.",
    sentiment: "negative",
    risk: {
      high: 30,
      medium: 50,
      low: 20,
    },
  },
];