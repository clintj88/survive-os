import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { BookOpen, Droplets, Beef, Stethoscope, Home, Flame, Compass, Wrench, Dog, Sprout, Radio, Shield, Scale, ArrowLeft, Search } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/education')({
  component: Education,
})

const CATEGORIES = [
  { id: 'water', title: 'Water Purification', icon: Droplets, count: 8, desc: 'Filtration, distillation, and testing methods' },
  { id: 'food', title: 'Food Preservation', icon: Beef, count: 12, desc: 'Canning, drying, smoking, and fermentation' },
  { id: 'firstaid', title: 'First Aid', icon: Stethoscope, count: 15, desc: 'Wound care, splints, CPR, and triage' },
  { id: 'shelter', title: 'Shelter Building', icon: Home, count: 6, desc: 'Construction, insulation, and weatherproofing' },
  { id: 'fire', title: 'Fire Starting', icon: Flame, count: 5, desc: 'Friction, flint, and fire management' },
  { id: 'nav', title: 'Navigation', icon: Compass, count: 7, desc: 'Map reading, compass use, and celestial navigation' },
  { id: 'tools', title: 'Tool Maintenance', icon: Wrench, count: 9, desc: 'Sharpening, repair, and tool making' },
  { id: 'animals', title: 'Animal Husbandry', icon: Dog, count: 10, desc: 'Livestock care, breeding, and veterinary basics' },
  { id: 'crops', title: 'Crop Management', icon: Sprout, count: 14, desc: 'Planting, soil health, and pest control' },
  { id: 'radio', title: 'Radio Operations', icon: Radio, count: 4, desc: 'Meshtastic, ham radio, and protocol' },
  { id: 'security', title: 'Security Protocols', icon: Shield, count: 6, desc: 'Patrol procedures, threat assessment' },
  { id: 'governance', title: 'Community Governance', icon: Scale, count: 3, desc: 'Decision-making, conflict resolution' },
]

const ARTICLES: Record<string, { title: string; summary: string; author: string; updated: string; content: string }[]> = {
  water: [
    { title: 'Boiling Water for Safety', summary: 'The simplest and most reliable method of water purification.', author: 'Chen, W.', updated: 'Mar 5', content: 'Bring water to a rolling boil for at least 1 minute (3 minutes above 6,500 ft elevation). This kills bacteria, viruses, and parasites. Let cool before drinking. Store in clean, covered containers.' },
    { title: 'DIY Sand Filter Construction', summary: 'Build a biosand filter from locally available materials.', author: 'Thompson, A.', updated: 'Feb 20', content: 'Layer gravel, coarse sand, and fine sand in a container. Water percolates through layers, removing 98% of bacteria. Requires 2-3 weeks to develop biofilm. Flow rate: ~1 liter per minute.' },
  ],
  firstaid: [
    { title: 'Wound Cleaning and Closure', summary: 'Proper irrigation and closure techniques for lacerations.', author: 'Garcia, M.', updated: 'Mar 8', content: 'Irrigate with clean water or saline under pressure. Remove debris. For shallow cuts, use butterfly strips. For deeper wounds, suture if trained. Apply antibiotic ointment and sterile dressing. Change dressing daily.' },
  ],
}

function Education() {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [selectedArticle, setSelectedArticle] = useState<number | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  const articles = selectedCategory ? (ARTICLES[selectedCategory] ?? []) : []
  const article = selectedArticle !== null ? articles[selectedArticle] : null

  if (article && selectedCategory) {
    return (
      <>
        <Header />
        <Main>
          <Button variant='ghost' size='sm' className='mb-4' onClick={() => setSelectedArticle(null)}>
            <ArrowLeft className='size-4 mr-1' /> Back to articles
          </Button>
          <h1 className='text-[22px] font-bold mb-2'>{article.title}</h1>
          <p className='text-xs text-muted-foreground mb-4'>By {article.author} — Updated {article.updated}</p>
          <div className='prose prose-invert prose-sm max-w-none'>
            <p className='text-sm leading-relaxed text-zinc-300'>{article.content}</p>
          </div>
        </Main>
      </>
    )
  }

  if (selectedCategory) {
    const cat = CATEGORIES.find((c) => c.id === selectedCategory)
    return (
      <>
        <Header />
        <Main>
          <Button variant='ghost' size='sm' className='mb-4' onClick={() => { setSelectedCategory(null); setSelectedArticle(null) }}>
            <ArrowLeft className='size-4 mr-1' /> Back to categories
          </Button>
          <h1 className='text-[22px] font-bold mb-1'>{cat?.title}</h1>
          <p className='text-[13px] text-muted-foreground mb-4'>{cat?.desc}</p>
          {articles.length === 0 ? (
            <div className='text-center py-12 text-muted-foreground'>No articles yet in this category.</div>
          ) : (
            <div className='space-y-2'>
              {articles.map((a, i) => (
                <Card key={i} className='cursor-pointer hover:bg-muted/30 transition-colors' onClick={() => setSelectedArticle(i)}>
                  <CardContent className='py-3'>
                    <div className='font-medium text-sm'>{a.title}</div>
                    <div className='text-xs text-muted-foreground mt-1'>{a.summary}</div>
                    <div className='text-[10px] text-zinc-600 mt-1'>By {a.author} — {a.updated}</div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </Main>
      </>
    )
  }

  return (
    <>
      <Header />
      <Main>
        <div className='mb-5'>
          <div className='flex items-center justify-between'>
            <div>
              <h1 className='text-[22px] font-bold tracking-tight'>Knowledge Base</h1>
              <p className='text-[13px] text-muted-foreground mt-1'>Survival knowledge and community reference materials</p>
            </div>
          </div>
        </div>

        <div className='relative max-w-sm mb-6'>
          <Search className='absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground' />
          <Input placeholder='Search knowledge base...' value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className='pl-9' />
        </div>

        <div className='grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3'>
          {CATEGORIES.filter((c) => c.title.toLowerCase().includes(searchQuery.toLowerCase())).map((cat) => {
            const Icon = cat.icon
            return (
              <Card key={cat.id} className='cursor-pointer hover:bg-muted/30 transition-colors' onClick={() => setSelectedCategory(cat.id)}>
                <CardContent className='pt-4 pb-3 text-center'>
                  <div className='mx-auto mb-2 flex size-10 items-center justify-center rounded-lg bg-muted'>
                    <Icon className='size-5 text-amber-500' />
                  </div>
                  <div className='text-sm font-medium'>{cat.title}</div>
                  <div className='text-[10px] text-muted-foreground mt-1'>{cat.count} articles</div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </Main>
    </>
  )
}
