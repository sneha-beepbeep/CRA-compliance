// Illustrative content for the SME checklist demo.
// The product's own item wording and citations are still placeholders pending
// a legal sanity-check, so these questions and rules were written for this
// demo only. They show how the checklist works; they are not legal guidance.
// Rule format mirrors the product (items.en.json): combos of answers that give
// "compliant" or "not_compliant"; "*" matches any answer (demo shorthand).
// Anything unmatched, or any "not_sure", gives "needs_check".
window.DEMO_DATA = {
  business: 'Lindenhof Bakery (fictional)',
  qualifying: 'Does your website include any AI-generated content (text, images, chat, audio or video)?',
  items: [
    {
      id: 'text', title: 'AI-written text',
      statement: 'If your site publishes text written with AI, some kinds of it may need to be disclosed to readers.',
      questions: [
        { id: 'q1', text: 'Do you publish text written or drafted with AI (for example blog posts or news updates)?' },
        { id: 'q2', text: 'Does that text carry a visible note that AI was used?' },
      ],
      compliantWhen: [{ q1: 'no', q2: '*' }, { q1: 'yes', q2: 'yes' }],
      notCompliantWhen: [],
      // yes/no is left unmatched on purpose: whether disclosure is needed depends on
      // facts a checklist can't see (topic, human editorial review), so it falls to Needs-check.
      sample: { q1: 'yes', q2: 'no' },
    },
    {
      id: 'images', title: 'AI-generated images',
      statement: 'AI-generated or AI-edited images that could pass as real photos may need to be labelled.',
      questions: [
        { id: 'q1', text: 'Does your site use AI-generated or AI-edited images?' },
        { id: 'q2', text: 'Are those images labelled as AI-generated where they appear?' },
      ],
      compliantWhen: [{ q1: 'no', q2: '*' }, { q1: 'yes', q2: 'yes' }],
      notCompliantWhen: [],
      sample: { q1: 'yes', q2: 'yes' },
    },
    {
      id: 'chat', title: 'Chat and support widgets',
      statement: 'People talking to an automated chat assistant should be told they are dealing with an AI system.',
      questions: [
        { id: 'q1', text: 'Does your site have a chat or support widget answered by an AI system?' },
        { id: 'q2', text: 'Does it tell visitors, before or at the start of the chat, that they are talking to an AI?' },
      ],
      compliantWhen: [{ q1: 'no', q2: '*' }, { q1: 'yes', q2: 'yes' }],
      notCompliantWhen: [{ q1: 'yes', q2: 'no' }],
      sample: { q1: 'yes', q2: 'no' },
    },
    {
      id: 'media', title: 'Synthetic audio and video',
      statement: 'Audio or video that makes it look or sound as if a real person said or did something ("deepfakes") must be disclosed as artificially generated.',
      questions: [
        { id: 'q1', text: 'Does your site publish AI-generated audio or video showing realistic people or voices?' },
        { id: 'q2', text: 'Is it clearly labelled as AI-generated?' },
      ],
      compliantWhen: [{ q1: 'no', q2: '*' }, { q1: 'yes', q2: 'yes' }],
      notCompliantWhen: [{ q1: 'yes', q2: 'no' }],
      sample: { q1: 'no', q2: 'no' },
    },
  ],
};
