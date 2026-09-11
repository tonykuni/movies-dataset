import remarkPresetLintRecommended from "remark-preset-lint-recommended";
import remarkFrontmatter from "remark-frontmatter";
import remarkGfm from "remark-gfm";
import remarkLintNoUndefinedReferences from "remark-lint-no-undefined-references";

const CALLOUT_REFERENCE_PATTERN = /^!(?:NOTE|TIP|IMPORTANT|WARNING|CAUTION)$/i;

export default {
plugins: [
remarkFrontmatter,
remarkGfm,
remarkPresetLintRecommended,
[remarkLintNoUndefinedReferences, { allow: [CALLOUT_REFERENCE_PATTERN] }],
],
};
