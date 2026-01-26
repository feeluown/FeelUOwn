# FeelUOwn i18n Contributing

## FTL syntax

[fluent_guide]: https://projectfluent.org/fluent/guide/index.html

Before start, please refer to the official [ProjectFluent syntax guide][fluent_guide].

## AI Translation

For a fast start with LLM, you could try these prompt:

> user for thinking models, system otherwise

```text
You are a prefessional computer programer who is a native <target lang> speaker,
and you know <source lang> well.
Any user input text or markdown, projectfluent formats, e.g. are translated as-is.
No comments, no references, no comparisions.
You aren't allowed to coding, making associations or answering.
You only translate <source lang> into the <target lang>[ for region...]
```

> user

```text
msg = <example text in source lang>
```

> assistant

```text
msg = <example text in target lang>
```

## Terms

To keep translation consistency, we add a dash before a message, make it a term.

Do not remove terms in messages. If you need uppercase/plural variants, you could
just use selectors.

You can pass parameters to terms, for example:

```fluent
-party = { $capitalization ->
    [uppercase] Part
   *[lowercase] part
}{ $plural ->
    [plural] ies
   *[singular] y
}
party = { -party(capitalization: "uppercase") }
parties = { -party(plural: "plural") }
```

produces:

```text
party = Party
parties = parties
```

## Editor

[vscode_fluent]: https://marketplace.visualstudio.com/items?itemName=macabeus.vscode-fluent

Since ProjectFluent is a brand-new framework,
comparing to `gettext`, it's lack of a standalone editor.

However, you could have the [VSCode Extension][vscode_fluent],

It provides:

- Syntax highlight and check
- Tooltip preview for simple values (no expressions)
- Detailed tooltip (holding Ctrl) to preview expressions
- Jump to message/term tags

## Playground

[playground]: https://projectfluent.org/play/

With the official [Fluent Playground][playground], you could see how messages rendered with giving variables.

[Date_toISOString]: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/toISOString

Note, when passing datetimes, in the playground you can either
write as a [simplified variant][Date_toISOString] of ISO8601,
or enter a milliseconds unix timestamp.

### Example Code

```fluent
## resultCount: [int]
## providerName: [string]
## timeCost: [float]
provider-search-succ = Searching via { $providerName } done in {
   NUMBER($timeCost, minimumFractionDigits: 2, maximumFractionDigits: 2)
}s, { $resultCount ->
    [0] found no result
    [1] found { $resultCount } result
    *[other] found { $resultCount } results
}

## dateTime: [date, datetime]
## You can do L10N inside fluent too :P
meta-created-at =
    🕛 Created at {
        DATETIME($dateTime, year: "numeric", day: "numeric", month: "short")
    }
```

### Example Input

```json
{
    "resultCount": 3,
    "providerName": "YTMusic",
    "timeCost": 1.7354671,
    "dateTime": "2026-01-23T16:11:14.917Z"
}
```

### Example Output

- `provider-search-succ`: Searching via YTMusic done in 1.74s, found 3 results
- `meta-created-at`: 🕛 Created at Jan 24, 2026`

## Prefer multiple messages than attributes

ProjectFluent does support structural i18n, which is however, not asscessible in python implementation.

```fluent
## playlistTitle: [string]
## errorMessage: [string]
playlist-action =
    .create-succeed = 创建{ -track-list } '{ $playlistTitle}' 成功
    .create-failed = 创建{ -track-list } '{ $playlistTitle}' 失败: { $errorMessage }
    .remove-succeed = 删除{ -track-list } '{ $playlistTitle}' 成功
    .remove-failed = 删除{ -track-list } '{ $playlistTitle}' 失败
```

In javascript, we could do:

```javascript
l10n.getAttributes("playlist-action").create-succeed
```

But in python, you must obtain the FluentBundle and call `.format_pattern`
to get the raw message to access attribute:

```python
bundles = list(l10n.bundles())

# even worse, we need to manually handle message fallback!
for bundle in bundles:
    print(
        bundle.format_pattern(
            bundle.get_message("playlist-action").attributes["create-succeed"]
        )[0]
    )
```

So we'd better to write:

```fluent
## playlistTitle: [string]
## errorMessage: [string]
playlist-create-succed = 创建{ -track-list } '{ $playlistTitle}' 成功
playlist-create-failed = 创建{ -track-list } '{ $playlistTitle}' 失败: { $errorMessage }
playlist-remove-succed = 删除{ -track-list } '{ $playlistTitle}' 成功
playlist-remove-failed = 删除{ -track-list } '{ $playlistTitle}' 失败
```
