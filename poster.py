from poster_maker.creator import AthleteRankPosterGenerator
from poster_maker.saver import PosterSaver


class PosterAthletesCollector:
    """Collect and generate posters for athletes."""

    def __init__(self, athletes_data):
        self.athletes_data = athletes_data
        self.poster_generator = AthleteRankPosterGenerator()
        self.saver = PosterSaver()

    def _group_athletes_for_posters(self):
        """Group athletes for generating posters."""
        top_10 = self.athletes_data[:10]
        remainder = self.athletes_data[10:]
        tag = len(remainder) - (len(remainder) % 15)
        groups = [top_10] + [remainder[i:i+15] for i in range(0, tag, 15)]
        return groups

    async def create_and_save_posters(self):
        """Create and save posters for grouped athletes."""
        groups = self._group_athletes_for_posters()
        await self.saver.clear_output_folder()

        for num, group in enumerate(groups):
            is_head_icon = num == 0
            filename = f"poster_{num + 1}.png"
            poster = await self.poster_generator.generate_poster(
                group, is_head_icon
            )
            await self.saver.save_poster(poster, filename)

        await self.poster_generator.close()
