-- Pandoc optional filter: retain Microsoft/GitHub callout markers as literal text.

local CALLOUT_PATTERN = "^%[!(%u+)%]"

function defBlockQuote(element)
  if #element.content == 0 or element.content[1].t ~= "Para" then
    return nil
  end
  local text = pandoc.utils.stringify(element.content[1])
  if string.match(text, CALLOUT_PATTERN) then
    return element
  end
  return nil
end

return {
  { BlockQuote = defBlockQuote }
}
