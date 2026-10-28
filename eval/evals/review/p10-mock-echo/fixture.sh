#!/bin/bash
set -euo pipefail
cp -cR /Users/kentaro/Desktop/_lab/ai/skills-eval-app/. .
git add -A >/dev/null
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "fixture" --allow-empty
mkdir -p "$(dirname 'src/features/products/ProductSearch.calls.test.tsx')"
cat > 'src/features/products/ProductSearch.calls.test.tsx' <<'EOF_FIXTURE'
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { searchProducts } from "../../api/products";
import { ProductSearch } from "./ProductSearch";

vi.mock("../../api/products", () => ({
  searchProducts: vi.fn().mockResolvedValue([]),
}));

describe("ProductSearch の検索", () => {
  it("入力したキーワードで検索する", async () => {
    const user = userEvent.setup();
    render(<ProductSearch />);

    await user.type(screen.getByLabelText("キーワード"), "モニター");
    await user.click(screen.getByRole("button", { name: "検索" }));

    expect(searchProducts).toHaveBeenCalledTimes(1);
    expect(searchProducts).toHaveBeenCalledWith("モニター");
  });
});
EOF_FIXTURE
