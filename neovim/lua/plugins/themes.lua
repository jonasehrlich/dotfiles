Github = {
  "projekt0n/github-nvim-theme",
  priority = 1000,
  config = function()
    require("github-theme").setup({})
    vim.cmd("colorscheme github_dark")
  end,
}

OneDarkPro = {
  "olimorris/onedarkpro.nvim",
  priority = 1000, -- Ensure it loads first
  config = function()
    require("onedarkpro").setup({})
    vim.cmd("colorscheme onedarkpro")
  end,
}

return {
  Github,
}
